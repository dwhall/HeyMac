#!/usr/bin/env python3
"""
Copyright 2019 Dean Hall.  See LICENSE for details.

Data Link Layer (LNK) state machine for Carrier-Sense Multiple Access (CSMA)
- listens for beacons and maintains a neighbors list
- periodically transmits a beacon frame and an extended beacon frame
"""


import logging

import farc
import phy_sx127x

from . import lnk_frame


class LnkHeymac(object):
    """HeyMac link layer (LNK) protocol values.
    """
    # The number of seconds between each emission of a beacon.
    # This value also affects the time a node spends lurking.
    _BCN_PRD = 32

    # The LoRa Sync Word is a SX127x register setting
    # that lets the hardware discriminate for frames
    # that have like Sync Words.
    # This value is differs from power-up and LoRaWAN values,
    # but is otherwise an arbitrary choice: ASCII 'H'
    _HEYMAC_SYNC_WORD = 0x48

    # PHY settings
    _PHY_STNGS_DFLT = (
        ("FLD_RDO_LORA_MODE", 1),
        ("FLD_RDO_FREQ", 432_550_000),
        ("FLD_RDO_MAX_PWR", 7),
        ("FLD_RDO_PA_BOOST", 1),
        ("FLD_LORA_BW", 8), # phy_sx127x.PhySX127x.STNG_LORA_BW_250K
        ("FLD_LORA_SF", 7), # phy_sx127x.PhySX127x.STNG_LORA_SF_128_CPS
        ("FLD_LORA_CR", 2), # phy_sx127x.PhySX127x.STNG_LORA_CR_4TO6
        ("FLD_LORA_CRC_EN", 1),
        ("FLD_LORA_SYNC_WORD", _HEYMAC_SYNC_WORD),
    )
    _PHY_STNGS_RX = (("FLD_RDO_FREQ", 432_550_000),)
    _PHY_STNGS_TX = (("FLD_RDO_FREQ", 432_550_000),)


class LnkHeymacCsmaAhsm(LnkHeymac, farc.Ahsm):
    """The link layer (LNK) state machine automates
    medium access and frame I/O processing.
    """

    def __init__(self, lnk_addr, station_id):
        """Class intialization
        """
        super().__init__()

        # Instantiate the lower layer
        self.phy_ahsm = phy_sx127x.PhySX127xAhsm(True)
        self.phy_ahsm.set_dflt_stngs(LnkHeymac._PHY_STNGS_DFLT)
        self.phy_ahsm.set_dflt_rx_clbk(self._phy_rx_clbk)

        # TODO: these go in mac data?
        self._lnk_addr = lnk_addr
        self._station_id = station_id # UNUSED


#### Public interface

    def start_stack(self, ahsm_prio, delta_prio=10):
        """Starts the lower layer giving it a higher priority (lower number)
        and then starts this Ahsm
        """
        assert delta_prio > 0, "Lower layer must have higher priority (lower number)"
        assert ahsm_prio - delta_prio > 0, "Priorty must not go below zero"
        self.phy_ahsm.start_stack(ahsm_prio - delta_prio)
        self.start(ahsm_prio)


#### State machine

    @farc.Hsm.state
    def _initial(self, event):
        """PseudoState: _initial
        State machine framework initialization
        """
        # Self-signaling
        farc.Signal.register("_ALWAYS")

        # Self-signaling events
        self._evt_always = farc.Event(farc.Signal._ALWAYS, None)

        # Timer events
        self.bcn_evt = farc.TimeEvent("_LNK_BCN_TMOUT")
        self.tm_evt = farc.TimeEvent("_LNK_TMOUT")

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
            #self.lnk_data = lnk_csma_data.LnkData()

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
    def _running(self, event):
        """State: _running
        Receives continuously for two beacon periods
        - any tx-packet request is enqueued (no transmissions at this level)
        - accepts GPS NMEA events to get position information
        - accepts SIGTERM event to force an exit
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("LNK._running")
            return self.handled(event)

        elif sig == farc.Signal.EXIT:
            logging.debug("LNK._running @EXIT")
            # TODO: request phy_sleep
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _lurking(self, event):
        """State: _running:_lurking
        Waits for a fixed period with the receiver enabled
        then transitions to the _beaconing state
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("LNK._lurking")
            self.tm_evt.post_in(self, LnkHeymac._BCN_PRD)
            return self.handled(event)

        elif sig == farc.Signal._LNK_TMOUT:
            return self.tran(self._beaconing)

        elif sig == farc.Signal.EXIT:
            self.tm_evt.disarm()
            return self.handled(event)

        return self.super(self._running)


    @farc.Hsm.state
    def _beaconing(self, event):
        """State: _running:_beaconing
        - periodically transmits a beacon
        - transitions to _networking state when bidirectional path discovered
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("LNK._beaconing")
            self.bcn_evt.post_every(self, LnkHeymac._BCN_PRD)
            self._tx_bcn()
            return self.handled(event)

        elif sig == farc.Signal._LNK_BCN_TMOUT:
            logging.debug("LNK._beaconing@TMOUT")
            self._tx_bcn()
            return self.handled(event)

        elif sig == farc.Signal.EXIT:
            self.bcn_evt.disarm()
            return self.handled(event)

        return self.super(self._running)


    @farc.Hsm.state
    def _networking(self, event):
        """State: _running:_beaconing:_networking
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("LNK._networking")
            return self.handled(event)

        return self.super(self._running)


#### Private methods

    def _tx_bcn(self,):
        """Builds a Heymac CsmaBeacon and passes it to the PHY for transmit.
        """
        frame = lnk_frame.HeymacFrame(
            lnk_frame.HeymacFrame.PID_IDENT_HEYMAC | lnk_frame.HeymacFrame.PID_TYPE_CSMA,
            lnk_frame.HeymacFrame.FCTL_L | lnk_frame.HeymacFrame.FCTL_S)
        frame.set_field(lnk_frame.HeymacFrame.FLD_SADDR, self._lnk_addr)
        frame.set_field(lnk_frame.HeymacFrame.FLD_PAYLD, b"BEACON BEACON BEACON BEACON") #lnk_cmds.HeyMacCmdCbcn( caps=0, status=0 ))
        self.phy_ahsm.post_tx_action(self.phy_ahsm.TM_NOW, LnkHeymac._PHY_STNGS_TX, bytes(frame))


    def _phy_rx_clbk(self, rx_time, rx_bytes, rx_rssi, rx_snr):
        """A method given to the PHY layer as a callback.
        The PHY calls this method with these arguments
        when it receives a frame with no errors.
        This method puts the arguments in a container
        and posts a _LNK_RX_FROM_PHY to this state machine.
        """
        logging.debug("LNK:_phy_rx_clbk")
