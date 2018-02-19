#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.

MAC (data link layer) (layer 2) State Machine for protocol operations
- listens for PPS signal and RX packet times to synchronize to a network
- selects an appropriate Timeslot to periodically transmit a beacon frame
- maintains a schedule of transmit and receive Timeslots
- maintains a list of neighbors with link quality stats
"""


import hashlib, math

import pq

import mac_cfg, mac_cmds, mac_frame
import phy_cfg
import cfg


# Turn user JSON config files into Python dicts
mac_identity = cfg.get_from_json("mac_identity.json")
# Convert hex bytes to bytearray since JSON can't do binary strings
mac_identity['pub_key'] = bytearray.fromhex(mac_identity['pub_key'])


class HeyMacAhsm(pq.Ahsm):

    @staticmethod
    def initial(me, event):
        """Pseudostate: HeyMacAhsm:initial
        """
        # Outgoing signals
        pq.Signal.register("GPS_NMEA") # Value is one NMEA sentence [bytes]

        # Incoming signals
        pq.Framework.subscribe("PHY_GPS_PPS", me)
        pq.Framework.subscribe("PHY_RX_DATA", me)

        # Initialize a timer event
        me.tm_evt = pq.TimeEvent("MAC_TMR_PRDC")
        
        # Calculate the 128-bit source address from the identity's pub_key
        h = hashlib.sha512()
        h.update(mac_identity['pub_key'])
        h.update(h.digest())
        me.saddr = h.digest()[:8]
        assert me.saddr[0] in (0xfc, 0xfd)
        
        # Init HeyMac values
        me.asn = 0
        me.bcn_seq = 0
        me.bcn_slot = mac_identity['pub_key'][0] % mac_cfg.tslots_per_sframe

        # Error of computer clock time [secs]
        # calculated as: time_at_pps - prev_time_at_pps
        me.pps_err = 0.0

        # Time of the previous GPS PPS
        me.time_of_last_pps = None

        return me.tran(me, HeyMacAhsm.initializing)


    @staticmethod
    def initializing(me, event):
        """State: HeyMacAhsm:initializing
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            pq.Framework.post(pq.Event(pq.Signal.CFG_LORA, phy_cfg.sx127x_cfg), "SX127xSpiAhsm")
            me.postFIFO(pq.Event(pq.Signal.ALWAYS, None))
            return me.handled(me, event)

        elif sig == pq.Signal.ALWAYS:
            return me.tran(me, HeyMacAhsm.listening)

        elif sig == pq.Signal.EXIT:
            return me.handled(me, event)

        return me.super(me, me.top)


    @staticmethod
    def running(me, event):
        """State: HeyMacAhsm:running
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            return me.handled(me, event)

        elif sig == pq.Signal.PHY_GPS_PPS:
            print("pps            ", event.value)
            me.on_pps(event.value)
            return me.handled(me, event)

        elif sig == pq.Signal.PHY_RX_DATA:
            rx_time, payld, rssi, snr = event.value
            me.on_rx_frame(rx_time, payld, rssi, snr)
            return me.handled(me, event)

        elif sig == pq.Signal.SIGTERM:
            return me.tran(me, me.exiting)

        elif sig == pq.Signal.EXIT:
            return me.handled(me, event)

        return me.super(me, me.top)


    @staticmethod
    def listening(me, event):
        """State: HeyMacAhsm:running:listening
        Listens to radio and GPS for timing indicators.
        Transitions to Scheduling after listening for two superframes
        """
        N_SFRAMES = 0.1 # 1.0
        LISTEN_PRD_SECS = 0.750
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("LISTENING")
            me.tm_evt.postEvery(me, LISTEN_PRD_SECS)  # TODO: ensure this is longer than the rx timeout
            me.tries = int(N_SFRAMES * mac_cfg.tslots_per_sframe / mac_cfg.tslots_per_sec / LISTEN_PRD_SECS)
            return me.handled(me, event)

        elif sig == pq.Signal.MAC_TMR_PRDC:
            me.tries -= 1
            if me.tries == 0:
                return me.tran(me, me.scheduling)
            else:
                value = (0, phy_cfg.rx_freq) # rx time and freq
                pq.Framework.post(pq.Event(pq.Signal.RECEIVE, value), "SX127xSpiAhsm")
            return me.handled(me, event)

        elif sig == pq.Signal.EXIT:
            del me.tries
            me.tm_evt.disarm()
            return me.handled(me, event)

        return me.super(me, me.running)


    @staticmethod
    def scheduling(me, event):
        """State: HeyMacAhsm:running:scheduling
        Emits beacon regularly.
        If this node has received beacons, an open slot is chosen;
        otherwise, the slot is chosen arbitrarily.
        If this node has received PPS, tx and rx timeslots are synchronized.
        """
        # The following value was determined through experimentation to cause
        # the least amount of error (PHY rx_time - GPS PPS), 3.8 ms on avg.
        TSLOT_PREP_TIME = 0.040 # secs.

        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("SCHEDULING")
            
            now = pq.Framework._event_loop.time()

            # If there has been no PPS, use now as a pseudo edge
            if not me.time_of_last_pps:
                me.time_of_last_pps = now
                me.tslots_since_last_pps = 0

            # If there has been a PPS, initialize this variable
            else:
                me.tslots_since_last_pps = math.floor((now - me.time_of_last_pps) * mac_cfg.tslots_per_sec)

                # If no rx'd MAC frames have updated the ASN, init it to match latest PPS edge
                if me.asn == 0:
                    me.asn = me.tslots_since_last_pps

            print("entry          ", now)
            print("asn            ", me.asn)

            # Set the TimeEvent to expire at the next Prep Time
            me.next_tslot = me.time_of_last_pps + (1 + me.tslots_since_last_pps) * (1.0 - me.pps_err) / mac_cfg.tslots_per_sec
            me.tm_evt.postAt(me, me.next_tslot - TSLOT_PREP_TIME)

            return me.handled(me, event)

        elif sig == pq.Signal.MAC_TMR_PRDC:
            """Handler for the periodic timer which is set to elapse at TSLOT_PREP_TIME
            number of seconds before the beginning of every Tslot.  This "prep time"
            allows the scheduler to select the MAC action for the next Tslot and
            optionally message the physical layer.  If active, the PHY will do
            some preparation which reduces its warm-up time (allowing more precise
            control of TX and RX time).
            """
            # Count the Absolute Slot Number
            me.asn += 1

#            print("prep           ", pq.Framework._event_loop.time())

            # Transmit a beacon during this node's beacon slot
            if me.asn % mac_cfg.tslots_per_sframe == me.bcn_slot:
                me.tx_bcn(me.next_tslot)

            # Listen after every PPS
            elif me.asn % 4 == 0:
                value = (me.next_tslot, phy_cfg.rx_freq) # rx time and freq
                pq.Framework.post(pq.Event(pq.Signal.RECEIVE, value), "SX127xSpiAhsm")

            # Do nothing during this Tslot
            else:
                pass

            # Count this Tslot and set the TimeEvent to expire at the next Prep Time
            me.tslots_since_last_pps += 1
            me.next_tslot = me.time_of_last_pps + (1 + me.tslots_since_last_pps) * (1.0 - me.pps_err) / mac_cfg.tslots_per_sec
            me.tm_evt.postAt(me, me.next_tslot - TSLOT_PREP_TIME)

            return me.handled(me, event)

        elif sig == pq.Signal.EXIT:
            me.tm_evt.disarm()
            return me.handled(me, event)

        return me.super(me, me.running)

    @staticmethod
    def exiting(me, event):
        """State HeyMacAhsm:exiting
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            return me.handled(me, event)
        
        return me.super(me, me.top)


#### End State Machines

    def build_mac_frame(self, seq=0):
        """Returns a generic HeyMac V1 frame with the given sequence number
        """
        frame = mac_frame.HeyMacFrame(fctl=mac_frame.FCTL_TYPE_MAC
            | mac_frame.FCTL_LENCODE_BIT
            | mac_frame.FCTL_SADDR_MODE_64BIT)
        frame.saddr = self.saddr
        frame.seq = seq
        return frame


    def on_pps(self, time_of_pps):
        """Measures the amount of computer clock time that has elapsed
        since the previous GPS PPS pulse.  Calculates the amount of error 
        between the computer clock time and the PPS edge.
        (self.pps_err).
        """
        # If there are two PPS pulses within the following amount of time [secs],
        # then use the delta between PPS pulses to calculate the
        # computer clock time per second.
        PPS_GAP_TOLERANCE = 10.0

        if self.time_of_last_pps:
            delta = time_of_pps - self.time_of_last_pps
            if delta < PPS_GAP_TOLERANCE:

                # Remove the whole seconds and divide by the number of secs
                # to get the amount of error per second
                whole_secs = round(delta)
                err = (delta - whole_secs) / whole_secs

                # TODO: least squares fit
                # For now, do this cheap IIR average
                self.pps_err = (self.pps_err + err) * 0.5

        # Save this one for the next time
        self.time_of_last_pps = time_of_pps

        # Reset this counter used in scheduling state
        self.tslots_since_last_pps = 0


    def on_rx_frame(self, rx_time, payld, rssi, snr):
        """
        """
        f = mac_frame.HeyMacFrame(bytes(payld))
        if isinstance(f.data, mac_cmds.HeyMacCmdBeacon):
            print("MAC_TMR_PRDC Rx %d bytes, rssi=%d dBm, snr=%.3f dB\t%s" % (len(payld), rssi, snr, repr(f)))
            # TODO: add to ngbr data
        else:
            print("rxd pkt is not a bcn")


    def tx_bcn(self, abs_time):
        """Builds a HeyMac V1 Beacon and passes it to the PHY for transmit.
        """
        frame = self.build_mac_frame(self.bcn_seq)
        bcn = mac_cmds.HeyMacCmdBeacon(asn=self.asn)
        frame.data = bcn
        tx_args = (abs_time, phy_cfg.tx_freq, bytes(frame)) # tx time, freq and data
        pq.Framework.post(pq.Event(pq.Signal.TRANSMIT, tx_args), "SX127xSpiAhsm")
        self.bcn_seq += 1
