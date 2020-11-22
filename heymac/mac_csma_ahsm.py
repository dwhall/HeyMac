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
import phy_sx127x

from . import mac_csma_data
from . import mac_csma_cfg
from . import mac_cmds
from . import mac_frame
from . import phy_cfg


class HeyMacCsmaAhsm(farc.Ahsm):
    def __init__(self, saddr, station_id):
        super().__init__()

        # TODO: this is not where this belongs,
        # it will move in the future
        # when I find it a new home
        # PHY default settings
        phy_dflt_stngs = (
            ("FLD_RDO_LORA_MODE", 1),
            ("FLD_RDO_FREQ", 432550000),
            ("FLD_RDO_MAX_PWR", 7),
            ("FLD_RDO_PA_BOOST", 1),
            ("FLD_LORA_BW", 8), # phy_sx127x.PhySX127x.STNG_LORA_BW_250K
            ("FLD_LORA_SF", 7), # phy_sx127x.PhySX127x.STNG_LORA_SF_128_CPS
            ("FLD_LORA_CR", 2), # phy_sx127x.PhySX127x.STNG_LORA_CR_4TO6
            ("FLD_LORA_CRC_EN", 1),
            ("FLD_LORA_SYNC_WORD", 0x48),  # FIXME: magic number
        )

        # Instantiate the lower layer
        self.phy_ahsm = phy_sx127x.PhySX127xAhsm(True)
        self.phy_ahsm.set_dflt_stngs(phy_dflt_stngs)

        # TODO: these go in mac data?
        self.saddr = saddr
        self.station_id = station_id


#### Public interface

    def start_stack(self, ahsm_prio, delta_prio=10):
        """Starts the lower layer giving it a higher priority (lower number)
        and then starts this Ahsm
        """
        assert delta_prio > 0, "Lower layer must have higher priority (lower number)"
        assert ahsm_prio - delta_prio > 0, "Priorty must not go below zero"
        self.phy_ahsm.start_stack(ahsm_prio - delta_prio)
        self.start(ahsm_prio)


#### Private methods

    def _phy_rx_clbk(self, frame_bytes, rx_time, rssi, snr):
        """A callback that is given to the PHY layer
        for it to call when a received frame and associated data
        are valid and should be delivered to the LNK layer.
        """
        # TODO: implement a real callback
        print("DWH: rx_clbk", frame_baytes, rx_time, rssi, snr)


#### State machine

    @farc.Hsm.state
    def _initial(self, event):
        """Pseudostate: HeyMacCsmaAhsm:_initial
        """
        # Incoming signals
        farc.Signal.register("MAC_TX_REQ")
        farc.Framework.subscribe("PHY_GPS_NMEA", self)
        farc.Framework.subscribe("PHY_RXD_DATA", self)
        farc.Framework.subscribe("PHY_TX_DONE", self)

        # Initialize timer events
        self.bcn_evt = farc.TimeEvent("_MAC_BCN_EVT_TMOUT")
        self.tm_evt = farc.TimeEvent("_MAC_TM_EVT_TMOUT")

        return self.tran(self._initializing)


    @farc.Hsm.state
    def _initializing(self, event):
        """State: HeyMacCsmaAhsm:_initializing
        - initializes MAC related variables and the tx-pkt queue
        - always transitions to the _lurking state
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("INITIALIZING")

            # Data Link Layer data
            self.mac_csma_data = mac_csma_data.MacData()

            # Transmit queue
            self.mac_txq = []

            self.post_fifo(farc.Event(farc.Signal._ALWAYS, None))
            return self.handled(event)

        elif sig == farc.Signal._ALWAYS:
            return self.tran(self._lurking)

        elif sig == farc.Signal.EXIT:
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _running(self, event):
        """State: HeyMacCsmaAhsm:_running
        The _running state:
        - receives continuously for two beacon periods
        - any tx-packet request is enqueued (no transmissions at this level)
        - accepts GPS NMEA events to get position information
        - accepts SIGTERM event to force an exit
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return self.handled(event)

        elif sig == farc.Signal.PHY_RXD_DATA:
            rx_time, payld, rssi, snr = event.value
            self._on_rxd_frame(rx_time, payld, rssi, snr)
            _receive_cont(phy_cfg.rx_freq)
            return self.handled(event)

        elif sig == farc.Signal.MAC_TX_REQ:
            # This low-level state should just enqueue pkts
            # because the active state may be _lurking.
            self.mac_txq.insert(0, event.value) # TODO: _networking state should periodically monitor & fwd
            return self.handled(event)

        elif sig == farc.Signal.PHY_GPS_NMEA:
            self.gps_gprmc = event.value
            return self.handled(event)

        elif sig == farc.Signal.SIGTERM:
            return self.tran(self._exiting)

        elif sig == farc.Signal.EXIT:
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _lurking(self, event):
        """State: HeyMacCsmaAhsm:_running:_lurking
        Passively receives radio and GPS for a fixed period
        (two beacon cycles) to build neighbor list,
        then transitions to the _beaconing state
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("LURKING")
            _receive_cont(phy_cfg.rx_freq)
            listening_period = mac_csma_cfg.BEACON_PERIOD_SEC
            self.tm_evt.post_in(self, listening_period)
            return self.handled(event)

        elif sig == farc.Signal._MAC_TM_EVT_TMOUT:
            # listening timer has expired, transition to _beaconing
            return self.tran(self._beaconing)

        elif sig == farc.Signal.EXIT:
            # Cancel the timer in case of a forced exit
            self.tm_evt.disarm()
            return self.handled(event)

        return self.super(self._running)


    @farc.Hsm.state
    def _beaconing(self, event):
        """State: HeyMacCsmaAhsm:_running:_beaconing
        - periodically transmits a beacon
        - transitions to _networking state when bidirectional path discovered
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("BEACONING")
            self.bcn_evt.post_every(self, mac_csma_cfg.BEACON_PERIOD_SEC)
            self.tm_evt.post_every(self, 1.0)
            return self.handled(event)

        elif sig == farc.Signal.PHY_RXD_DATA:
            # Process the received frame just like in _running state
            rx_time, payld, rssi, snr = event.value
            self._on_rxd_frame(rx_time, payld, rssi, snr)
            _receive_cont(phy_cfg.rx_freq)

            # Transition to _networking if a bidirectional path is discovered
            if self._ngbr_hears_me():
                return self.tran(self._networking)
            else:
                return self.handled(event)

        elif sig == farc.Signal._MAC_BCN_EVT_TMOUT:
            # Transmit a std beacon during this node's beacon slot
            logging.info("bcn")
            self._tx_bcn()
            return self.handled(event)

        elif sig == farc.Signal.PHY_TX_DONE:
            # After a beacon is transmitted, go back to receiving continuously
            _receive_cont(phy_cfg.rx_freq)
            return self.handled(event)

        elif sig == farc.Signal._MAC_TM_EVT_TMOUT:
            self._attempt_tx_from_q()
            return self.handled(event)

        elif sig == farc.Signal.EXIT:
            self.bcn_evt.disarm()
            return self.handled(event)

        return self.super(self._running)


    @farc.Hsm.state
    def _networking(self, event):
        """State: HeyMacCsmaAhsm:_running:_beaconing:_networking
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("NETWORKING")

        elif sig == farc.Signal.PHY_RXD_DATA:
            rx_time, payld, rssi, snr = event.value
            self._on_rxd_frame(rx_time, payld, rssi, snr)
            return self.handled(event)

        return self.super(self._running)


    @farc.Hsm.state
    def _exiting(self, event):
        """State HeyMacCsmaAhsm:_exiting
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("EXITING")
            return self.handled(event)

        return self.super(self.top)


#### End State Machines

    def _on_rxd_frame(self, rx_time, payld, rssi, snr):
        """This function is called when the PHY layer has received a frame
        and passed it to the MAC layer.
        The frame is validated and collected into a frame_info.
        The frame is processed according to whether it is MAC or NET layer.
        Processing may involve consuming, forwarding or dropping the frame.
        """
        try:
            f = mac_frame.HeyMacFrame(bytes(payld))
        except:
            logging.warning("rxd pkt failed header validation or unpacking")
            return

        if f.pid_type != mac_frame.HeyMacFrame.PID_TYPE_CSMA:
            logging.warning("rxd pkt is not HeyMac CSMA")
            return

        if not f.is_heymac_version_compatible():
            logging.warning("rxd pkt has incompatible HeyMac version")
            return

        logging.info(
            "rx_time        %f\tRXD %d bytes, rssi=%d dBm, snr=%.3f dB\t%s",
            rx_time, len(payld), rssi, snr, repr(f))

        frame_info = mac_frame.FrameInfo(f, rx_time, rssi, snr)

        # If frame is a MAC cmd
        if f.is_data_mac_layer():
            # If this node should process the frame
            # (frame addressed to this node
            # TODO: or frame is flood/broadcast)
            if f.daddr == self.saddr:
                self._process_mac_frame(frame_info)

            # If this node should resend the frame
            # (frame is not addressed to this node and is multihop and
            # TODO: not in recent frame list)
            if (f.daddr != self.saddr
                and f.fctl_m != 0):
                # reduce hop count
                f.hops -= 1
                # apply my address
                f.txaddr = self.saddr
                # put pkt in txq
                self.mac_txq.append(f)

        # Else if the frame is a NET pkt
        elif f.is_data_net_layer():
            # TODO:
            # If this node should process the frame
            # (frame addressed to this node or frame is flood/broadcast)
            # If this node should resend the frame
            self.process_net_pkt(f, rx_time)

        # else:
        #   if I should forward frame:
        #       reduce hop count
        #       apply my address
        #       put pkt in txq


    def _tx_bcn(self,):
        """Builds a HeyMac CsmaBeacon and passes it to the PHY for transmit.
        """
        frame = mac_frame.HeyMacFrame()
        frame.saddr = self.saddr
        frame.data = mac_cmds.HeyMacCmdCbcn(
            caps=0,
            status=0,
                        )
        #tx_args = (-1, phy_cfg.tx_freq, bytes(frame)) # immediate transmit
        #farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_TRANSMIT, tx_args), "SX127xSpiAhsm")
        tx_stngs = (("FLD_RDO_FREQ", phy_cfg.tx_freq),)
        self.phy_ahsm.enqueue_for_tx(bytes(frame), self.phy_ahsm.ENQ_TM_NOW, tx_stngs)


    def _attempt_tx_from_q(self,):
        """Creates a frame, inserts the payload that is next in the queue
        and dispatches the frame to the PHY for transmission.
        Assumes caller checked that the queue is not empty.
        """
        # TODO: check that phy layer has not received a header
        if self.mac_txq:
            logging.info("tx from q")
            frame = mac_frame.HeyMacFrame()
            frame.data = self.mac_txq.pop()
            #tx_args = (-1, phy_cfg.tx_freq, bytes(frame)) # tx immediately, freq and data
            #farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_TRANSMIT, tx_args), "SX127xSpiAhsm")
            tx_stngs = (("FLD_RDO_FREQ", phy_cfg.tx_freq),)
            self.phy_ahsm.enqueue_for_tx(bytes(frame), -1, tx_stngs)


    def _ngbr_hears_me(self,):
        """Returns True if at least one neighbor lists this node
        in its neighbor list; proving two-way transmission has taken place.
        """
        ngbr_cbcns = self.mac_csma_data.get_cbcns()
        for ngbr, cbcn in ngbr_cbcns.items():
            if cbcn.valid:
                for n in cbcn.value.ngbrs:
                    if n[0] == self.saddr:
                        return True
        return False


    def _process_mac_frame(self, frame_info):
        """Processes the frame according to its MAC cmd.
        """
        f = frame_info.frame
        if isinstance(f.payld, mac_cmds.HeyMacCmdCbcn):
            self.mac_csma_data.process_beacon(frame_info)


## Convenience functions

def _receive_cont(freq):
    """Commands the modem to receive-continuous mode
    """
# TODO: this goes away after SX127xSpiAhsm is able to init with rx-cont setting
#    farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_RECEIVE, (-1, freq)), "SX127xSpiAhsm")
