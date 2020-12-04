#!/usr/bin/env python3
"""
Copyright 2019 Dean Hall.  See LICENSE for details.

Data Link Layer (LNK) state machine for Carrier-Sense Multiple Access (CSMA)
radio operations using Heymac frame protocol.
- listens for beacons and maintains a neighbors list with link stats
- periodically transmits a beacon frame
"""


import logging

import farc
import phy_sx127x

from . import lnk_frame


class LnkHeymac(object):
    """Heymac link layer (LNK) protocol values."""
    # The number of seconds between each emission of a beacon.
    # This value also affects the time a node spends lurking.
    _BCN_PRD = 32

    # The LoRa Sync Word is a SX127x register setting
    # that lets the hardware discriminate for frames
    # that have like Sync Words.
    # This value differs from power-up and LoRaWAN values,
    # but is otherwise an arbitrary choice: ASCII 'H'
    _HEYMAC_SYNC_WORD = 0x48

    # PHY settings
    _PHY_STNGS_DFLT = (
        ("FLD_RDO_LORA_MODE", 1),
        ("FLD_RDO_FREQ", 432_550_000),
        ("FLD_RDO_MAX_PWR", 7),
        ("FLD_RDO_PA_BOOST", 1),
        ("FLD_LORA_BW", 8),     # phy_sx127x.PhySX127x.STNG_LORA_BW_250K
        ("FLD_LORA_SF", 7),     # phy_sx127x.PhySX127x.STNG_LORA_SF_128_CPS
        ("FLD_LORA_CR", 2),     # phy_sx127x.PhySX127x.STNG_LORA_CR_4TO6
        ("FLD_LORA_CRC_EN", 1),
        ("FLD_LORA_SYNC_WORD", _HEYMAC_SYNC_WORD),
    )
    _PHY_STNGS_RX = (("FLD_RDO_FREQ", 432_550_000),)
    _PHY_STNGS_TX = (("FLD_RDO_FREQ", 432_550_000),)


class LnkHeymacCsmaAhsm(LnkHeymac, farc.Ahsm):
    """The link layer (LNK) state machine.

    Automates beaconing and frame processing.
    """

    def __init__(self, lnk_addr, station_id):
        """Class intialization
        """
        super().__init__()

        # Instantiate the lower layer
        self.phy_ahsm = phy_sx127x.PhySX127xAhsm(True)
        self.phy_ahsm.set_dflt_stngs(LnkHeymac._PHY_STNGS_DFLT)
        self.phy_ahsm.set_dflt_rx_clbk(self._phy_rx_clbk)

        # TODO: these go in lnk data?
        self._lnk_addr = lnk_addr
        self._station_id = station_id   # UNUSED


# Public interface


    def start_stack(self, ahsm_prio, delta_prio=10):
        """Starts this layer of the network stack.

        This layer must start the lower layer,
        giving it a higher priority (lower number)
        and then starts this layer's state machine.
        """
        assert delta_prio > 0, \
            "Lower layer must have higher priority (lower number)"
        assert ahsm_prio - delta_prio > 0, "Priorty must not go below zero"
        self.phy_ahsm.start_stack(ahsm_prio - delta_prio)
        self.start(ahsm_prio)


# State machine


    @farc.Hsm.state
    def _initial(self, event):
        """PseudoState: _initial

        State machine framework initialization
        """
        # Self-signaling
        farc.Signal.register("_ALWAYS")
        farc.Signal.register("_LNK_RXD_FROM_PHY")

        # Self-signaling events
        self._evt_always = farc.Event(farc.Signal._ALWAYS, None)

        # Timer events
        self._bcn_evt = farc.TimeEvent("_LNK_BCN_TMOUT")

        return self.tran(self._initializing)


    @farc.Hsm.state
    def _initializing(self, event):
        """State: _initializing

        Application initialization.
        Initializes LNK data and the pkt queue.
        Always transitions to the _lurking state.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("LNK._initializing")

            # Data Link Layer data
            # self.lnk_data = lnk_csma_data.LnkData()

            # Transmit queue
            self.mac_txq = []

            self.post_fifo(self._evt_always)
            return self.handled(event)

        elif sig == farc.Signal._ALWAYS:
            return self.tran(self._lurking)

        elif sig == farc.Signal.EXIT:
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _lurking(self, event):
        """State: _lurking

        Waits for a fixed period with the receiver enabled,
        processes any received frames, and then
        transitions to the _beaconing state
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("LNK._lurking")
            self._bcn_evt.post_in(self, 2 * LnkHeymac._BCN_PRD)
            return self.handled(event)

        elif sig == farc.Signal._LNK_BCN_TMOUT:
            return self.tran(self._beaconing)

        elif sig == farc.Signal._LNK_RXD_FROM_PHY:
            self._on_rxd_from_phy(event.value)
            return self.handled(event)

        elif sig == farc.Signal.EXIT:
            self._bcn_evt.disarm()
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _beaconing(self, event):
        """State: _lurking:_beaconing

        Periodically transmits a beacon
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("LNK._beaconing")
            self._bcn_evt.post_every(self, LnkHeymac._BCN_PRD)
            self._post_bcn()
            return self.handled(event)

        elif sig == farc.Signal._LNK_BCN_TMOUT:
            logging.debug("LNK._beaconing@BCN_TMOUT")
            self._post_bcn()
            return self.handled(event)

        elif sig == farc.Signal.EXIT:
            self._bcn_evt.disarm()
            return self.handled(event)

        return self.super(self._lurking)


    @farc.Hsm.state
    def _networking(self, event):
        """State: _lurking:_beaconing:_networking"""
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("LNK._networking")
            return self.handled(event)

        return self.super(self._beaconing)


# Private methods

    def _on_rxd_from_phy(self, rxd_data):
        """Processes a frame received from the PHY."""
        try:
            rx_time, rx_bytes, rx_rssi, rx_snr = rxd_data
            frame = lnk_frame.HeymacFrame.parse(rx_bytes)
            frame.rx_time = rx_time
            frame.rx_rssi = rx_rssi
            frame.rx_snr = rx_snr
        except lnk_frame.HeymacFrameError:
            logging.info("LNK:rxd frame is not valid Heymac\n\t{}"
                         .format(rx_bytes))
            # TODO: lnk stats incr rxd frame is not Heymac
            return

        # TODO:
        # If payld is Heymac command
            # If this frame is meant for this node (addr, bcast or mcast)
                # Process Heymac command
                    # If response frame, transmit it
            # If this node should re-transmit the frame
        # elif payld is NET layer
            # Pass frame to NET layer


    def _phy_rx_clbk(self, rx_time, rx_bytes, rx_rssi, rx_snr):
        """A method given to the PHY layer as a callback.

        The PHY calls this method with these arguments
        when it receives a frame with no errors.
        This method collects the arguments in a container
        and posts an event to this state machine.
        """
        rxd_data = (rx_time, rx_bytes, rx_rssi, rx_snr)
        self.post_fifo(farc.Event(farc.Signal._LNK_RXD_FROM_PHY, rxd_data))


    def _post_bcn(self,):
        """Builds a Heymac CsmaBeacon and posts it to the PHY for transmit."""
        frame = lnk_frame.HeymacFrame(
            lnk_frame.HeymacFrame.PID_IDENT_HEYMAC
            | lnk_frame.HeymacFrame.PID_TYPE_CSMA,
            lnk_frame.HeymacFrame.FCTL_L
            | lnk_frame.HeymacFrame.FCTL_S)
        frame.set_field(lnk_frame.HeymacFrame.FLD_SADDR, self._lnk_addr)
        frame.set_field(  # lnk_cmds.HeyMacCmdCbcn( caps=0, status=0 ))
            lnk_frame.HeymacFrame.FLD_PAYLD, b"BEACON BEACON BEACON BEACON")
        self.phy_ahsm.post_tx_action(
            self.phy_ahsm.TM_NOW,
            LnkHeymac._PHY_STNGS_TX,
            bytes(frame))
