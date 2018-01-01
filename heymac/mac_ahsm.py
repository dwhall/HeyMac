#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.

MAC (data link layer) (layer 2) State Machine for protocol operations
- listens for PPS signal and RX packet times to synchronize to a network
- selects an appropriate Timeslot to periodically transmit a beacon frame
- maintains a schedule of transmit and receive Timeslots
- maintains a list of neighbors with link quality stats
"""


import pq

import mac_cfg, phy_cfg


class HeyMacAhsm(pq.Ahsm):

    @staticmethod
    def initial(me, event):
        """Pseudostate: HeyMacAhsm:initial
        """
        # Outgoing signals
        pq.Signal.register("GPS_NMEA") # Value is one NMEA sentence [bytes]

        # Incoming signals
        pq.Framework.subscribe("PHY_RX_DATA", me)

        # Initialize a timer event used to schedule the NMEA handler
        me.tm_evt = pq.TimeEvent("MAC_TMR_PRDC")
        
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
        Exits due to one of three conditions:
        1) PPS signals are present and have listened for one Sframe
        2) RXd data frames and have sync'd to neighbors' beacons
        3) No signals and one Sframe has elapsed
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("MAC LISTENING")
            me.tm_evt.postEvery(me, 0.750)
            me.tries = int(mac_cfg.tslots_per_sframe / mac_cfg.tslots_per_sec / 0.750)
            return me.handled(me, event)

        elif sig == pq.Signal.MAC_TMR_PRDC:
            print("post receive")
            value = (0, phy_cfg.rx_freq) # rx time and freq
            pq.Framework.post(pq.Event(pq.Signal.RECEIVE, value), "SX127xSpiAhsm")
            me.tries -= 1
            if me.tries == 0:
                return me.tran(HeyMacAhsm.beaconing)
            return me.handled(me, event)

        elif sig == pq.Signal.PHY_RX_DATA:
            print("rx_data", event.value)
            return me.handled(me, event)

        elif sig == pq.Signal.EXIT:
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


