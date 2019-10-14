#!/usr/bin/env python3
"""
Copyright 2019 Dean Hall.  See LICENSE for details.

Data Link Layer (layer 2) Medium Access Control (MAC)
State Machine for Carrier-Sense Multiple Access (CSMA):
- listens for beacons from neighbors
- periodically transmits a beacon frame and an extended beacon frame
- maintains a list of neighbors with link quality stats
"""


import logging

import farc

from . import mac_data
from . import mac_csma_cfg
from . import mac_cmds
from . import mac_frame
from . import phy_cfg


class HeyMacCsmaAhsm(farc.Ahsm):
    def __init__(self, saddr, station_id):
        super().__init__()

        self.saddr = saddr
        self.station_id = station_id


    @farc.Hsm.state
    def _initial(me, event):
        """Pseudostate: HeyMacCsmaAhsm:_initial
        """
        # Incoming signals
        farc.Signal.register("MAC_TX_REQ")
        farc.Framework.subscribe("PHY_RXD_DATA", me)
        farc.Framework.subscribe("PHY_GPS_NMEA", me)

        # Initialize timer events
        me.bcn_evt = farc.TimeEvent("_MAC_BCN_EVT_TMOUT")
        me.tm_evt = farc.TimeEvent("_MAC_TM_EVT_TMOUT")

        return me.tran(me, HeyMacCsmaAhsm._initializing)


    @farc.Hsm.state
    def _initializing(me, event):
        """State: HeyMacCsmaAhsm:_initializing
        - initializes MAC related variables and the tx-pkt queue
        - always transitions to the _listening state
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("INITIALIZING")

            # Data Link Layer data
            me.mac_data = mac_data.MacData()

            # Transmit queue
            me.mac_txq = []

            me.postFIFO(farc.Event(farc.Signal._ALWAYS, None))
            return me.handled(me, event)

        elif sig == farc.Signal._ALWAYS:
            return me.tran(me, HeyMacCsmaAhsm._listening)

        elif sig == farc.Signal.EXIT:
            return me.handled(me, event)

        return me.super(me, me.top)


    @farc.Hsm.state
    def _running(me, event):
        """State: HeyMacCsmaAhsm:_running
        The _running state:
        - receives continuously for two beacon periods
        - any tx-packet request is enqueued (no transmissions at this level)
        - accepts GPS NMEA events to get position information
        - accepts SIGTERM event to force an exit
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return me.handled(me, event)

        elif sig == farc.Signal.PHY_RXD_DATA:
            rx_time, payld, rssi, snr = event.value
            me._on_rxd_frame(rx_time, payld, rssi, snr)
            # immediate rx continuous
            rx_args = (-1, phy_cfg.rx_freq)
            farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_RECEIVE, rx_args), "SX127xSpiAhsm")
            return me.handled(me, event)

        elif sig == farc.Signal.MAC_TX_REQ:
            # This low-level state should just enqueue pkts
            # because the active state may be _listening.
            me.mac_txq.insert(0, event.value) # TODO: _networking state should periodically monitor & fwd
            return me.handled(me, event)

        elif sig == farc.Signal.PHY_GPS_NMEA:
            me.gps_gprmc = event.value
            return me.handled(me, event)

        elif sig == farc.Signal.SIGTERM:
            return me.tran(me, me._exiting)

        elif sig == farc.Signal.EXIT:
            return me.handled(me, event)

        return me.super(me, me.top)


    @farc.Hsm.state
    def _listening(me, event):
        """State: HeyMacCsmaAhsm:_running:_listening
        - listens for a fixed period (two beacon cycles) to build neighbor list
        - transitions to _beaconing state
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("LISTENING")
            # rx continuously on the rx_freq
            value = (-1, phy_cfg.rx_freq)
            farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_RECEIVE, value), "SX127xSpiAhsm")
            listening_period = mac_csma_cfg.BEACON_PERIOD_SEC
            me.tm_evt.postIn(me, listening_period)
            return me.handled(me, event)

        elif sig == farc.Signal._MAC_TM_EVT_TMOUT:
            # listening timer has expired, transition to _beaconing
            return me.tran(me, me._beaconing)

        elif sig == farc.Signal.EXIT:
            # Cancel the timer in case of a forced exit
            me.tm_evt.disarm()
            return me.handled(me, event)

        return me.super(me, me._running)


    @farc.Hsm.state
    def _beaconing(me, event):
        """State: HeyMacCsmaAhsm:_running:_beaconing
        - periodically transmits a beacon
        - transitions to _networking state when bidirectional path discovered
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("BEACONING")
            me.bcn_evt.postEvery(me, mac_csma_cfg.BEACON_PERIOD_SEC)
            me.tm_evt.postEvery(me, 1.0)
            return me.handled(me, event)

        elif sig == farc.Signal.PHY_RXD_DATA:
            # Process the received frame just like in _running state
            rx_time, payld, rssi, snr = event.value
            me._on_rxd_frame(rx_time, payld, rssi, snr)
            # immediate rx continuous
            rx_args = (-1, phy_cfg.rx_freq)
            farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_RECEIVE, rx_args), "SX127xSpiAhsm")

            # Transition to _networking if a bidirectional path is discovered
            if me._ngbr_hears_me(me):
                return me.tran(me, HeyMacCsmaAhsm._networking)
            else:
                return me.handled(me, event)

        elif sig == farc.Signal._MAC_BCN_EVT_TMOUT:
            # Transmit a std beacon during this node's beacon slot
            logging.info("bcn")
            me._tx_bcn()
            # Resume continuous receive after beaconing
            rx_args = (-1, phy_cfg.rx_freq)
            farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_RECEIVE, rx_args), "SX127xSpiAhsm")
            return me.handled(me, event)

        elif sig == farc.Signal._MAC_TM_EVT_TMOUT:
            me._attempt_tx_from_q()
            return me.handled(me, event)

        elif sig == farc.Signal.EXIT:
            me.bcn_evt.disarm()
            return me.handled(me, event)

        return me.super(me, me._running)


    @farc.Hsm.state
    def _networking(me, event):
        """State: HeyMacCsmaAhsm:_running:_beaconing:_networking
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("NETWORKING")

        elif sig == farc.Signal.PHY_RXD_DATA:
            rx_time, payld, rssi, snr = event.value
            me._on_rxd_frame(me, rx_time, payld, rssi, snr)
            return me.handled(me, event)

        return me.super(me, me._running)


    @farc.Hsm.state
    def _exiting(me, event):
        """State HeyMacCsmaAhsm:_exiting
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("EXITING")
            return me.handled(me, event)

        return me.super(me, me.top)


#### End State Machines

    def _on_rxd_frame(self, rx_time, payld, rssi, snr):
        """This function is called when the PHY layer has received a frame
        and passed it to the MAC layer.
        """
        try:
            f = mac_frame.HeyMacFrame(bytes(payld))
        except:
            logging.warning("rxd pkt failed unpacking")
            return

        if not f.is_heymac_version_compatible():
            logging.warning("rxd pkt has incompatible version")
            return

        logging.info(
            "rx_time        %f\tRXD %d bytes, rssi=%d dBm, snr=%.3f dB\t%s",
            rx_time, len(payld), rssi, snr, repr(f))

        self.mac_data.process_heymac_frame(f)


    def _tx_bcn(self,):
        """Builds a HeyMac V1 CsmaBeacon and passes it to the PHY for transmit.
        """
        frame = mac_frame.HeyMacFrame()
        frame.fctl_type = mac_frame.HeyMacFrame.FCTL_TYPE_MAC
        frame.data = mac_cmds.HeyMacCmdCbcn(
#            dscpln=self.dscpln.get_dscpln_value(),
            caps=0,
            status=0,
# TODO        ngbr_data
# TODO        net_data
            )
        tx_args = (-1, phy_cfg.tx_freq, bytes(frame)) # immediate transmit
        farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_TRANSMIT, tx_args), "SX127xSpiAhsm")


    def _attempt_tx_from_q(self,):
        """Creates a frame, inserts the payload that is next in the queue
        and dispatches the frame to the PHY for transmission.
        Assumes caller checked that the queue is not empty.
        """
        # TODO: check that phy layer has not received a header
        if self.mac_txq:
            logging.info("tx from q")
            frame = mac_frame.HeyMacFrame()
            frame.fctl_type = mac_frame.HeyMacFrame.FCTL_TYPE_MAC
            frame.data = self.mac_txq.pop()
            tx_args = (-1, phy_cfg.tx_freq, bytes(frame)) # tx immediately, freq and data
            farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_TRANSMIT, tx_args), "SX127xSpiAhsm")


    def _ngbr_hears_me(self,):
        """Returns True if at least one neighbor lists this node
        in its neighbor list; proving two-way transmission has taken place.
        """
        ngbr_cbcns = self.mac_data.get_cbcns()
        for ngbr, cbcn in ngbr_cbcns.items():
            if cbcn.valid:
                for n in cbcn.value.ngbrs:
                    if n[0] == self.saddr:
                        return True
        return False
