"""
Copyright 2019 Dean Hall.  See LICENSE for details.

Data Link Layer (LNK) state machine for Carrier-Sense Multiple Access (CSMA)
radio operations using Heymac frame protocol.
- listens for beacons and maintains a neighbors list with link stats
- periodically transmits a beacon frame
"""


import logging

import farc

from .heymac_link import HeymacLink
from .heymac_frame import *
from .heymac_cmd import HeymacCmd, HeymacCmdError, HeymacCmdBcn
from ..utl import HamIdent


class Heymac():
    """Heymac link layer (LNK) protocol values."""
    # Link addresses are 8 octets in size
    # Heymac uses its long-address mode to convey a link address
    LNK_ADDR_SZ = 8

    # Link layer node capabilities (16 bit field).
    # These are bit flags used in the beacon's capabilities field.
    LNK_CAP_PWR = 0x0001        # Node has surplus power
    LNK_CAP_RXCONT = 0x0002     # Node is able to listen continuously
    LNK_CAP_CRYPTO = 0          # Node is capable of cryptographic routines
    # LNK_CAP_ROOT # No, this is net layer cap
    # LNK_CAP_NVSTO # Node has non-volatile storage (KBs? MBs? GBs?)

    # The number of seconds between each emission of a beacon.
    # This value also affects the time a node spends lurking.
    _BCN_PRD = 32

    # The number of seconds between each link update period in _linking()
    _LNK_UPDT_PRD = 4

    # The LoRa Sync Word is a SX127x register setting
    # that lets the hardware discriminate for frames
    # that have like Sync Words.
    # This value differs from power-up and LoRaWAN values,
    # but is otherwise an arbitrary choice: ASCII 'H'
    _HEYMAC_SYNC_WORD = 0x48

    # PHY settings
    _PHY_STNGS_DFLT = (
        ("FLD_RDO_LORA_MODE", 1),
        ("FLD_RDO_MAX_PWR", 7),
        ("FLD_RDO_PA_BOOST", 1),
        ("FLD_LORA_IMPLCT_HDR_MODE", 0),
        ("FLD_LORA_CRC_EN", 1),
        ("FLD_LORA_SYNC_WORD", _HEYMAC_SYNC_WORD),
    )
    _PHY_STNGS_RX = (("FLD_RDO_FREQ", 432_550_000),)
    _PHY_STNGS_TX = (("FLD_RDO_FREQ", 432_550_000),)


class HeymacCsmaHsm(farc.Ahsm):
    """The link layer (LNK) state machine.

    Automates beaconing and frame processing.
    """
    def __init__(self, phy):
        """Class intialization"""
        super().__init__()

        # Init the lower layer
        self._phy_hsm = phy
        self._phy_hsm.update_base_stngs(Heymac._PHY_STNGS_DFLT)
        self._phy_hsm.set_dflt_rx_clbk(self._phy_rx_clbk)

        self._rx_clbk = None


    def get_lnk_addr(self):
        return self._lnk_addr


    def send_cmd(self, cmd, dest=None):
        assert isinstance(cmd, HeymacCmd)

        f = HeymacFrame(HeymacFramePidType.CSMA)
        if dest:
            f.daddr = dest
        f.saddr = self._lnk_addr
        f.payld = bytes(cmd)
        self._phy_hsm.post_tx_action(self._phy_hsm.TM_NOW, None, bytes(f))


    def set_rx_clbk(self, rx_clbk):
        self._rx_clbk = rx_clbk


    def _get_credentials(self):
        """Attempt to get Crypto credentials."""
        cred = HamIdent.get_info_from_json_cred("HeyMac")
        if cred:
            self._callsign = cred["callsign"]
            self._pub_key = bytes.fromhex(cred["pub_key"])
            self._lnk_addr = HamIdent.get_addr("HeyMac", 64)
            self._lnk_data = HeymacLink(self._lnk_addr)


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
        self._tm_evt = farc.TimeEvent("_LNK_TMOUT")

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

        Waits with the receiver
        and a periodic timer enabled,
        processing any received frames.
        If identity credentials have been
        set when the periodic timer elapses,
        transitions to the _beaconing state.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("LNK._lurking")
            self._bcn_evt.post_in(self, 2 * Heymac._BCN_PRD)
            return self.handled(event)

        elif sig == farc.Signal._LNK_BCN_TMOUT:
            self._callsign = None
            self._get_credentials()
            if self._callsign:
                return self.tran(self._beaconing)
            else:
                self._bcn_evt.post_in(self, Heymac._BCN_PRD)
                return self.handled(event)

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

        Periodically transmits a beacon.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("LNK._beaconing")
            self._bcn_evt.post_every(self, Heymac._BCN_PRD)
            self._post_bcn()
            return self.handled(event)

        elif sig == farc.Signal._LNK_BCN_TMOUT:
            logging.debug("LNK._beaconing@BCN_TMOUT")
            self._post_bcn()
            return self.handled(event)

        elif sig == farc.Signal._LNK_RXD_FROM_PHY:
            self._on_rxd_from_phy(event.value)
            if self._lnk_data.ngbr_hears_me():
                return self.tran(self._linking)
            return self.handled(event)

        elif sig == farc.Signal.EXIT:
            self._bcn_evt.disarm()
            return self.handled(event)

        return self.super(self._lurking)


    @farc.Hsm.state
    def _linking(self, event):
        """State: _lurking:_beaconing:_linking

        Indicates at least one neighbor has this node in its neighbor's list.
        This state starts a periodic timer used to perform updates
        on the link data (such as prune the neighbor list).
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("LNK._linking")
            self._tm_evt.post_every(self, Heymac._LNK_UPDT_PRD)
            return self.handled(event)

        elif sig == farc.Signal._LNK_TMOUT:
            self._lnk_data.update()
            if not self._lnk_data.ngbr_hears_me():
                return self.tran(self._beaconing)
            return self.handled(event)

        elif sig == farc.Signal.EXIT:
            self._tm_evt.disarm()
            return self.handled(event)

        return self.super(self._beaconing)


# Private


    def _on_rxd_from_phy(self, frame):
        """Processes a frame received from the PHY."""
        assert type(frame) is HeymacFrame

        # Attach the Heymac command, if present
        try:
            cmd = HeymacCmd.parse(frame.payld)
        except HeymacCmdError:
            cmd = None
        frame.cmd = cmd

        # Process the frame for link data, etc.
        self._lnk_data.process_frame(frame)

        # If the frame is a multi-hop Heymac command
        if frame.cmd and frame.is_mhop():
            hops = frame.hops
            if hops > 1:
                # Update the hops and re-transmitter fields
                frame.hops = hops - 1
                frame.taddr = self._lnk_addr
                # Post the frame to PHY for transmission
                self._post_frm(frame)

        # Allow the NET layer to process the frame
        if self._rx_clbk:
            self._rx_clbk(frame)


    def _phy_rx_clbk(self, rx_time, rx_bytes, rx_rssi, rx_snr):
        """A method given to the PHY layer as a callback.

        The PHY calls this method with these arguments
        when it receives a frame with no errors.
        This method collects the arguments in a container
        and posts an event to this state machine.
        """
        # Parse the bytes into a frame
        # and store reception meta-data
        try:
            frame = HeymacFrame.parse(rx_bytes)
            frame.rx_meta = (rx_time, rx_rssi, rx_snr)
        except HeymacFrameError:
            logging.info("LNK:rxd frame is not valid Heymac\n\t{}"
                         .format(rx_bytes))
            # TODO: lnk stats incr rxd frame is not Heymac
            return

        # The frame is valid, post it to the state machine
        self.post_fifo(farc.Event(farc.Signal._LNK_RXD_FROM_PHY, frame))


    def _post_bcn(self):
        """Builds a Heymac CsmaBeacon and posts it to the PHY for transmit."""
        callsign = self._callsign.ljust(16).encode()

        bcn = HeymacCmdBcn(
            # TODO: Fill with real data
            caps=Heymac.LNK_CAP_RXCONT,
            status=0,
            callsign_ssid=callsign,
            pub_key=self._pub_key)
        frame = HeymacFrame(HeymacFramePidType.CSMA)
        frame.saddr = self._lnk_addr
        frame.payld = bytes(bcn)
        self._phy_hsm.post_tx_action(
            self._phy_hsm.TM_NOW,
            Heymac._PHY_STNGS_TX,
            bytes(frame))


    def _post_frm(self, frame):
        """Posts the frame to the PHY for transmit."""
        assert type(frame) is HeymacFrame
        self._phy_hsm.post_tx_action(
            self._phy_hsm.TM_NOW,
            Heymac._PHY_STNGS_TX,
            bytes(frame))
