#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.

MAC (data link layer) (layer 2) State Machine for protocol operations
- listens for PPS signal and RX packet times to synchronize to a network
- selects an appropriate Timeslot to periodically transmit a beacon frame
- maintains a schedule of transmit and receive Timeslots
- maintains a list of neighbors with link quality stats
"""


import hashlib

import pq

import mac_cfg, mac_cmds, mac_frame, mac_identity, phy_cfg


class HeyMacAhsm(pq.Ahsm):

    @staticmethod
    def initial(me, event):
        """Pseudostate: HeyMacAhsm:initial
        """
        # Outgoing signals
        pq.Signal.register("GPS_NMEA") # Value is one NMEA sentence [bytes]

        # Incoming signals
        pq.Framework.subscribe("PHY_PPS", me)
        pq.Framework.subscribe("PHY_RX_DATA", me)

        # Initialize a timer event used to schedule the NMEA handler
        me.tm_evt = pq.TimeEvent("MAC_TMR_PRDC")
        
        # Calculate the 128-bit source address from the identity's pub_key
        h = hashlib.sha512()
        h.update(mac_identity.pub_key)
        h.update(h.digest())
        me.saddr = h.digest()[:8]
        assert me.saddr[0] in (0xfc, 0xfd)
        
        # First estimate of 1s
        me.pps_est = 1.0

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
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("LISTENING")
            me.tm_evt.postEvery(me, 0.750)  # TODO: ensure this is longer than the rx timeout
            me.tries = int(1.0 * mac_cfg.tslots_per_sframe / mac_cfg.tslots_per_sec / 0.750)
            return me.handled(me, event)

        elif sig == pq.Signal.MAC_TMR_PRDC:
            value = (0, phy_cfg.rx_freq) # rx time and freq
            pq.Framework.post(pq.Event(pq.Signal.RECEIVE, value), "SX127xSpiAhsm")
            me.tries -= 1
            if me.tries == 0:
                return me.tran(me, me.scheduling)
            return me.handled(me, event)

        elif sig == pq.Signal.PHY_RX_DATA:
            rx_time, payld, rssi, snr = event.value
            f = mac_frame.HeyMacFrame(bytes(payld))
            if isinstance(f.data, mac_cmds.HeyMacCmdBeacon):
                print("lstng Rx %d bytes, rssi=%d dBm, snr=%.3f dB\t%s" % (len(payld), rssi, snr, repr(f)))
                # TODO: add to ngbr data
            else:
                print("rxd pkt is not a bcn")
            return me.handled(me, event)

        elif sig == pq.Signal.EXIT:
            del me.tries
            me.tm_evt.disarm()
            return me.handled(me, event)

        return me.super(me, me.top)


    @staticmethod
    def scheduling(me, event):
        """State: HeyMacAhsm:running:scheduling
        Emits beacon regularly.
        If this node has received beacons, an open slot is chosen;
        otherwise, the slot is chosen arbitrarily.
        If this node has received PPS, tx and rx timeslots are synchronized.
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("SCHEDULING")
            me.tslot_time = me.pps_est / mac_cfg.tslots_per_sec
            me.tm_evt.postIn(me, me.tslot_time)  # TODO: ensure this is longer than the rx timeout
            me.asn = 0
            me.bcn_seq = 0
            me.bcn_slot = mac_identity.pub_key[0] % mac_cfg.tslots_per_sframe
            return me.handled(me, event)

        elif sig == pq.Signal.MAC_TMR_PRDC:
            me.tm_evt.postIn(me, me.tslot_time)  # TODO: ensure this is longer than the rx timeout
            me.asn += 1
            if me.asn % mac_cfg.tslots_per_sframe == me.bcn_slot:
                print("bcn")
                value = (0, phy_cfg.tx_freq, me.build_beacon_cmd(me.bcn_seq)) # tx time, freq and data
                me.bcn_seq += 1
                pq.Framework.post(pq.Event(pq.Signal.TRANSMIT, value), "SX127xSpiAhsm")

            return me.handled(me, event)

        elif sig == pq.Signal.EXIT:
            me.tm_evt.disarm()
            return me.handled(me, event)

        return me.super(me, me.top)

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


    def build_beacon_cmd(self, bcn_seq=0):
        """Returns a HeyMac V1 Beacon frame with the given sequence number
        """
        f = self.build_mac_frame(bcn_seq)
        bcn = mac_cmds.HeyMacCmdBeacon(asn=self.asn)
        f.data = bcn
        return bytes(f)

