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
import cfg, lr


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
        pq.Framework.subscribe("PHY_RXD_DATA", me)

        # Initialize a timer event
        me.tm_evt = pq.TimeEvent("TM_EVT_TMOUT")
        
        # Calculate the 128-bit source address from the identity's pub_key
        h = hashlib.sha512()
        h.update(mac_identity['pub_key'])
        h.update(h.digest())
        me.saddr = h.digest()[:8]
        assert me.saddr[0] in (0xfc, 0xfd)
        
        # Init HeyMac values
        me.asn = 0
        me.bcn_seq = 0

        # This is the initial value for this node's beacon slot.
        # There may be a slot collision, so the final beacon slot may vary.
        # The first couple byte of this node's public key is a pseudo-random 
        # value to use to determine this node's Tslot to use for beaconing.
        me.bcn_slot = (mac_identity['pub_key'][0] << 8 | mac_identity['pub_key'][1]) \
                      % mac_cfg.TSLOTS_PER_SFRAME
        # Beacon slots are the first slots after a PPS
        me.bcn_slot = math.floor(me.bcn_slot / mac_cfg.TSLOTS_PER_SEC) * mac_cfg.TSLOTS_PER_SEC
        print("bcn_slot (%d / %d)" % (me.bcn_slot, mac_cfg.TSLOTS_PER_SFRAME))

        # Error of computer clock time [secs]
        # calculated as: time_at_pps - prev_time_at_pps
        me.pps_err = 0.0
        # Time of the previous GPS PPS
        me.time_of_last_pps = None

        # Error of computer clock time [secs]
        # calculated as: time_at_bcn - prev_time_at_bcn
        me.bcn_err = 0.0
        # Time of the previous BCN
        me.time_of_last_bcn = None

        # Linear Regression on CPU time when PPS arrives
        # using the 8 most recent data points
        pps_lr = lr.LinearRegression(8)

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
            me.on_pps(event.value)
            return me.handled(me, event)

        elif sig == pq.Signal.PHY_RXD_DATA:
            rx_time, payld, rssi, snr = event.value
            me.on_rxd_frame(rx_time, payld, rssi, snr)
            return me.handled(me, event)

        elif sig == pq.Signal.SIGTERM:
            return me.tran(me, me.exiting)

        elif sig == pq.Signal.EXIT:
            return me.handled(me, event)

        return me.super(me, me.top)


    @staticmethod
    def listening(me, event):
        """State: HeyMacAhsm:running:listening
        Listens to radio and GPS for timing discipline sources.
        Transitions to Scheduling after listening for N superframes.
        """
        N_SFRAMES_TO_LISTEN = 0.3 # 1.0

        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("LISTENING")
            value = (-1, phy_cfg.rx_freq) # rx continuously on the rx_freq
            pq.Framework.post(pq.Event(pq.Signal.RECEIVE, value), "SX127xSpiAhsm")
            listen_secs = N_SFRAMES_TO_LISTEN * mac_cfg.TSLOTS_PER_SFRAME / mac_cfg.TSLOTS_PER_SEC
            me.tm_evt.postIn(me, listen_secs)
            return me.handled(me, event)

        elif sig == pq.Signal.TM_EVT_TMOUT: # timer has expired
            # If two PPS have been received, transfer to scheduling state
            if me.pps_err:
                return me.tran(me, me.scheduling)
            else:
                print("remain listening")
                listen_secs = N_SFRAMES_TO_LISTEN * mac_cfg.TSLOTS_PER_SFRAME / mac_cfg.TSLOTS_PER_SEC
                me.tm_evt.postIn(me, listen_secs)
                return me.handled(me, event)
 
        elif sig == pq.Signal.PHY_RXD_DATA:
            # handle received frame
            rx_time, payld, rssi, snr = event.value
            me.on_rxd_frame(rx_time, payld, rssi, snr)

            # rx continuously again
            value = (-1, phy_cfg.rx_freq)
            pq.Framework.post(pq.Event(pq.Signal.RECEIVE, value), "SX127xSpiAhsm")
            return me.handled(me, event)

        # This handler is for debug-print only and may be removed
        elif sig == pq.Signal.PHY_GPS_PPS:
            print("pps            ", event.value)
            # process PPS in the running state, too
            return me.super(me, me.running)

        elif sig == pq.Signal.EXIT:
            # cancel continuous rx
            pq.Framework.post(pq.Event(pq.Signal.CANCEL, None), "SX127xSpiAhsm")
            return me.handled(me, event)

        return me.super(me, me.running)


    @staticmethod
    def scheduling(me, event):
        """State: HeyMacAhsm:running:scheduling
        Uses timing discipline to schedule packet tx and rx actions.
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            me.scheduling_and_entry(me)
            return me.handled(me, event)

        elif sig == pq.Signal.TM_EVT_TMOUT:
            me.scheduling_and_next_tslot(me)
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

    @staticmethod
    def scheduling_and_entry(self,):
        """Handler for the Scheduling state entry event.
        Uses timing discipline data to set a time event for the next Tslot.
        """
        print("SCHEDULING")

        now = pq.Framework._event_loop.time()

        # If there has been no PPS, use now as a pseudo edge
        if not self.time_of_last_pps:
            self.time_of_last_pps = now
            self.tslots_since_last_pps = 0

        # If there has been a PPS, initialize this variable
        else:
            self.tslots_since_last_pps = round((now - self.time_of_last_pps) * mac_cfg.TSLOTS_PER_SEC)

            # If no rx'd MAC frames have updated the ASN, init it to match latest PPS edge
            if self.asn == 0:
                self.asn = self.tslots_since_last_pps
        self._post_time_event_for_next_tslot(self)


    @staticmethod
    def scheduling_and_next_tslot(self,):
        """Handler for the Scheduling state when the next-slot-preparation timer
        has elapsed.  This method decides what to do in the next Tslot
        and messages the PHYsical layer with any actions.
        """
        # Increment the Absolute Slot Number and a Tslot counter
        self.asn += 1
        self.tslots_since_last_pps += 1

        # Transmit a beacon during this node's beacon slot
        if self.asn % mac_cfg.TSLOTS_PER_SFRAME == self.bcn_slot:
            print("bcn_tslot (pps)", self.next_tslot)
            self.tx_bcn(self.next_tslot)

        # TODO: send the top pkt in the tx que

        # Listen after every PPS (TODO: every tslot?)
        elif self.asn % 4 == 0:
            value = (self.next_tslot, phy_cfg.rx_freq) # rx time and freq
            pq.Framework.post(pq.Event(pq.Signal.RECEIVE, value), "SX127xSpiAhsm")

        # Do nothing during this Tslot
        else:
            pass

        # Count this Tslot and set the TimeEvent to expire at the next Prep Time
        self._post_time_event_for_next_tslot(self)


    @staticmethod
    def _post_time_event_for_next_tslot(self,):
        """Sets the TimeEvent to expire at the next Prep Time
        """
        TSLOT_PREP_TIME = 0.020 # secs.
        self.next_tslot = self.time_of_last_pps + (1 + self.tslots_since_last_pps) * (1.0 - self.pps_err) / mac_cfg.TSLOTS_PER_SEC
        self.tm_evt.postAt(self, self.next_tslot - mac_cfg.TSLOT_PREP_TIME)


    def build_mac_frame(self, seq=0):
        """Returns a generic HeyMac V1 frame with the given sequence number
        """
        frame = mac_frame.HeyMacFrame(fctl=mac_frame.FCTL_TYPE_MAC
            | mac_frame.FCTL_LENCODE_BIT
            | mac_frame.FCTL_SADDR_MODE_64BIT)
        frame.saddr = self.saddr
        frame.seq = seq
        return frame


    def calc_bcn_timing(self, time_of_bcn):
        """Measures the amount of computer clock time that has elapsed
        since the previous beacon.  Calculates the amount of error
        between the two and generates an average error, .bcn_err
        """
        # If there are two beacons within the following amount of time [secs],
        # then use the delta between beacons to calculate the
        # computer clock time per second.
        # (assumes beacons happen at top-of-second (same as PPS))
        BCN_GAP_TOLERANCE = 4 *  mac_cfg.TSLOTS_PER_SFRAME

        if self.time_of_last_bcn:
            delta = time_of_bcn - self.time_of_last_bcn
            if delta < BCN_GAP_TOLERANCE:

                # Remove the whole seconds and divide by the number of secs
                # to get the amount of error per second
                whole_secs = round(delta)
                err = (delta - whole_secs) / whole_secs

                # TODO: least squares fit
                # For now, do this cheap IIR average
                self.bcn_err = (self.bcn_err + err) * 0.5

        # Save this one for the next time
        self.time_of_last_bcn = time_of_bcn

        # Reset this counter used in scheduling state
        self.tslots_since_last_bcn = 0




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


    def on_rxd_frame(self, rx_time, payld, rssi, snr):
        """This function is called when the PHY layer has received a frame
        and passed it to the MAC layer.
        """
        try:
            f = mac_frame.HeyMacFrame(bytes(payld))
        except:
            print("rxd pkt failed unpacking")
            return

        if isinstance(f.data, mac_cmds.HeyMacCmdBeacon):
            self.calc_bcn_timing(rx_time)
            print("rx_time        ", rx_time,
                  "RXD %d bytes, rssi=%d dBm, snr=%.3f dB\t%s" % (len(payld), rssi, snr, repr(f)))
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
