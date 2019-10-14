#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.

Data Link Layer (layer 2) Medium Access Control (MAC)
State Machine for Time-Division Multiple Access (TDMA):
- listens for PPS signal and RX packet times to synchronize to a network
- selects an appropriate Timeslot to periodically transmit a beacon frame
- maintains a schedule of transmit and receive Timeslots
- maintains a list of neighbors with link quality stats
"""


import hashlib
import logging
import math
import socket

import farc

from . import mac_data
from . import mac_tdma_cfg
from . import mac_cmds
from . import mac_tdma_discipline
from . import mac_frame
from . import phy_cfg
from . import utl


# Turn user JSON config files into Python dicts
mac_identity = utl.get_from_json("HeyMac", "mac_identity.json")
# Convert hex bytes to bytearray since JSON can't do binary strings
mac_identity['pub_key'] = bytearray.fromhex(mac_identity['pub_key'])


class HeyMacAhsm(farc.Ahsm):

    @farc.Hsm.state
    def _initial(me, event):
        """Pseudostate: HeyMacAhsm:_initial
        """
        # Incoming signals
        farc.Signal.register("MAC_TX_REQ")
        farc.Framework.subscribe("PHY_GPS_PPS", me)
        farc.Framework.subscribe("PHY_RXD_DATA", me)
        farc.Framework.subscribe("PHY_GPS_NMEA", me)

        # Initialize a timer event
        me.tm_evt = farc.TimeEvent("_MAC_TDMA_TM_EVT_TMOUT")

        # Calculate the 128-bit source address from the identity's pub_key
        h = hashlib.sha512()
        h.update(mac_identity['pub_key'])
        h.update(h.digest())
        me.saddr = h.digest()[:8]
        assert me.saddr[0] in (0xfc, 0xfd)

        # Init HeyMac values
        me.asn = 0
        me.sf_order = mac_tdma_cfg.FRAME_SPEC_SF_ORDER
        me.eb_order = mac_tdma_cfg.FRAME_SPEC_EB_ORDER
        me.dscpln = mac_tdma_discipline.HeyMacDiscipline()

        # Data Link Layer data
        # TODO: network's SF/EB_ORDER values may change at runtime.
        #       Need to have mac_data's ValidatedDicts adapt.
        tm_tslot_period = (1.0 / mac_tdma_cfg.TSLOTS_PER_SEC)
        tm_sf_period = (2 ** mac_tdma_cfg.FRAME_SPEC_SF_ORDER) * tm_tslot_period
        tm_eb_period = (2 ** mac_tdma_cfg.FRAME_SPEC_EB_ORDER) * tm_sf_period
        bcn_expiration = 4 * tm_sf_period
        ebcn_expiration = 2 * tm_eb_period
        me.mac_data = mac_data.MacData(bcn_expiration, ebcn_expiration)

        # Transmit queue
        me.mac_txq = []

        return me.tran(me, HeyMacAhsm._initializing)


    @farc.Hsm.state
    def _initializing(me, event):
        """State: HeyMacAhsm:_initializing
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            me.postFIFO(farc.Event(farc.Signal._ALWAYS, None))
            return me.handled(me, event)

        elif sig == farc.Signal._ALWAYS:
            return me.tran(me, HeyMacAhsm._listening)

        elif sig == farc.Signal.EXIT:
            return me.handled(me, event)

        return me.super(me, me.top)


    @farc.Hsm.state
    def _running(me, event):
        """State: HeyMacAhsm:_running
        The _running state:
        - uses PPS events from the GPIO to establish timing discipline
        - receives continuously (hearing a ngbr will lead to state change)
        - uses GPS NMEA events to get position information
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return me.handled(me, event)

        elif sig == farc.Signal.PHY_GPS_PPS:
            time_of_pps = event.value
            me.dscpln.update_pps(time_of_pps)
            return me.handled(me, event)

        elif sig == farc.Signal.PHY_RXD_DATA:
            rx_time, payld, rssi, snr = event.value
            me.on_rxd_frame(me, rx_time, payld, rssi, snr)
            # immediate rx continuous
            rx_args = (-1, phy_cfg.rx_freq)
            farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_RECEIVE, rx_args), "SX127xSpiAhsm")
            return me.handled(me, event)

        elif sig == farc.Signal.MAC_TX_REQ:
            me.mac_txq.insert(0, event.value)
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
        """State: HeyMacAhsm:_running:_listening
        Listens to radio and GPS for timing discipline sources.
        Transitions to Scheduling after listening for N superframes.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("LISTENING")
            # rx continuously on the rx_freq
            value = (-1, phy_cfg.rx_freq)
            farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_RECEIVE, value), "SX127xSpiAhsm")
            listen_secs = mac_tdma_cfg.N_SFRAMES_TO_LISTEN * (2 ** me.sf_order) / mac_tdma_cfg.TSLOTS_PER_SEC
            me.tm_evt.postIn(me, listen_secs)
            return me.handled(me, event)

        elif sig == farc.Signal._MAC_TDMA_TM_EVT_TMOUT:
            # listening timer has expired, transition to _beaconing
            return me.tran(me, me._beaconing)

        # NOTE: This handler is for logging print and may be removed
        elif sig == farc.Signal.PHY_GPS_PPS: # GPS pulse per second pin event
            logging.info("pps            %f", event.value)
            # process PPS in the _running state, too
            return me.super(me, me._running)

        return me.super(me, me._running)


    @farc.Hsm.state
    def _beaconing(me, event):
        """State: HeyMacAhsm:_running:_beaconing
        Uses timing discipline to tx beacons.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("BEACONING")
            # Pick a beacon slot
            me.bcn_slot = me.pick_bcn_slot(me)
            logging.info("bcn_slot (%d / %d)" % (me.bcn_slot, 2 ** me.sf_order))
            # Calc the start of Tslots
            now = farc.Framework._event_loop.time()
            me.next_tslot = me.dscpln.get_time_of_next_tslot(now)
            logging.info("next_tslot = %f", me.next_tslot)
            me.tm_evt.postAt(me, me.next_tslot - mac_tdma_cfg.TSLOT_PREP_TIME)
            return me.handled(me, event)

        elif sig == farc.Signal._MAC_TDMA_TM_EVT_TMOUT:
            me.beaconing_and_next_tslot(me)
            if me.ngbr_hears_me(me):
                return me.tran(me, HeyMacAhsm._networking)
            else:
                return me.handled(me, event)

        elif sig == farc.Signal.EXIT:
            me.tm_evt.disarm()
            return me.handled(me, event)

        return me.super(me, me._running)


    @farc.Hsm.state
    def _networking(me, event):
        """State: HeyMacAhsm:_running:_beaconing:_networking
        Uses timing discipline to schedule packet tx and rx actions.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("NETWORKING")

        elif sig == farc.Signal.PHY_RXD_DATA:
            rx_time, payld, rssi, snr = event.value
            me.on_rxd_frame(me, rx_time, payld, rssi, snr)
            return me.handled(me, event)

        return me.super(me, me._running)


    @farc.Hsm.state
    def _exiting(me, event):
        """State HeyMacAhsm:_exiting
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.info("EXITING")
            return me.handled(me, event)

        return me.super(me, me.top)


#### End State Machines

    @staticmethod
    def beaconing_and_next_tslot(self,):
        """Handler for the Beaconing state when the next-slot-preparation timer
        has elapsed.  This method decides what to do in the next Tslot
        and messages the PHYsical layer with any actions.
        """
        # Increment the Absolute Slot Number and a Tslot counter
        self.asn += 1

        # Transmit an extended beacon during this node's beacon slot
        if self.asn % (2 ** self.sf_order * 2 ** self.eb_order) == self.bcn_slot:
            logging.info("ebcn_tslot     %f", self.next_tslot)
            self.tx_ebcn(self, self.next_tslot)

        # Transmit a std beacon during this node's beacon slot
        elif self.asn % (2 ** self.sf_order) == self.bcn_slot:
            logging.info("bcn_tslot      %f", self.next_tslot)
            self.tx_bcn(self, self.next_tslot)

        # Resume continuous receive after beaconing
        elif self.asn % (2 ** self.sf_order) == self.bcn_slot + 1:
            rx_args = (-1, phy_cfg.rx_freq)
            farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_RECEIVE, rx_args), "SX127xSpiAhsm")

        # Send the top pkt in the tx queue
        elif self.mac_txq:
            self.tx_from_txq(self, self.next_tslot)

        # Count this Tslot and set the TimeEvent to expire at the next Prep Time.
        # Sets the TimeEvent to expire at the next Prep Time.
        # When calculating next_tslot it is important to reference to the
        # source of absolute time (time of most recent PPS) so that there is
        # less accumulated error.
        now = farc.Framework._event_loop.time()
        self.next_tslot = self.dscpln.get_time_of_next_tslot(now)
        self.tm_evt.postAt(self, self.next_tslot - mac_tdma_cfg.TSLOT_PREP_TIME)


    @staticmethod
    def build_mac_frame(self,):
        """Returns a generic HeyMac frame
        """
        frame = mac_frame.HeyMacFrame()
        frame.fctl_type = mac_frame.HeyMacFrame.FCTL_TYPE_MAC
        return frame


    @staticmethod
    def on_rxd_frame(self, rx_time, payld, rssi, snr):
        """This function is called when the PHY layer has received a frame
        and passed it to the MAC layer.
        """
        try:
            f = mac_frame.HeyMacFrame(bytes(payld))
        except:
            logging.warning("rxd pkt failed unpacking")
            return

        if f.is_heymac_version_compatible():
            logging.info(
                "rx_time        %f\tRXD %d bytes, rssi=%d dBm, snr=%.3f dB\t%s",
                rx_time, len(payld), rssi, snr, repr(f))

            self.mac_data.process_heymac_frame(f)

            if f.is_bcn():
                self._on_rxd_mac_bcn(self, rx_time, f, rssi, snr)

        else:
            logging.warning("rxd pkt has unsupported/invalid PID/VER")


    @staticmethod
    def _on_rxd_mac_bcn(self, rx_time, frame, rssi, snr):
        """Handles reception of a beacon frame.
        Assumes caller has checked that frame is a beacon
        """
        bcn = frame.data

        # If the frame spec is incompatible
        if( bcn.sf_order != self.sf_order or bcn.eb_order != self.eb_order):
            # If the beaconer has the greater ASN, adopt its frame spec
            if bcn.asn > self.asn:
                self.sf_order = bcn.sf_order
                self.eb_order = bcn.eb_order
                logging.info("Adopting ngbr's frame spec: (SF=%d, EB=%d)" % (bcn.sf_order, bcn.eb_order))
            return

        # If the beacon has good discipline, measure it
        if bcn.dscpln >= mac_tdma_discipline.HeyMacDscplnEnum.PPS.value:
            logging.info("Adopting ngbr's timing discipline")
            self.dscpln.update_bcn(rx_time)

        # Adopt the greater ASN
        if bcn.asn > self.asn:
            logging.info("Adopting ngbr's ASN: %d (was: %d)" % (bcn.asn, self.asn))
            self.asn = bcn.asn


    @staticmethod
    def on_rxd_net_frame(self, rx_time, frame, rssi, snr):
        """Handles a frame designated for the network layer
        """
        pass


    @staticmethod
    def tx_bcn(self, abs_time):
        """Builds a HeyMac V1 Small Beacon and passes it to the PHY for transmit.
        """
        my_bcn_slotmap = bytearray((2 ** self.sf_order) // 8)
        my_bcn_slotmap[ self.bcn_slot // 8 ] |= (1 << (self.bcn_slot % 8))
        frame = self.build_mac_frame(self)
        frame.data = mac_cmds.HeyMacCmdSbcn(
            sf_order=self.sf_order,
            eb_order=self.eb_order,
            dscpln=self.dscpln.get_dscpln_value(),
            caps=0,
            status=0,
            asn=self.asn,
            tx_slots=my_bcn_slotmap, # FIXME
            ngbr_tx_slots=self.mac_data.get_bcn_slotmap(mac_tdma_cfg.FRAME_SPEC_SF_ORDER),
            )
        tx_args = (abs_time, phy_cfg.tx_freq, bytes(frame)) # tx time, freq and data
        farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_TRANSMIT, tx_args), "SX127xSpiAhsm")


    @staticmethod
    def tx_ebcn(self, abs_time):
        """Builds a HeyMac V1 Extended Beacon and passes it to the PHY for transmit.
        """
        my_bcn_slotmap = bytearray((2 ** self.sf_order) // 8)
        my_bcn_slotmap[ self.bcn_slot // 8 ] |= (1 << (self.bcn_slot % 8))
        frame = self.build_mac_frame(self)
        frame.data = mac_cmds.HeyMacCmdEbcn(
            sf_order=self.sf_order,
            eb_order=self.eb_order,
            dscpln=self.dscpln.get_dscpln_value(),
            caps=0,
            status=0,
            asn=self.asn,
            tx_slots=my_bcn_slotmap, # FIXME
            ngbr_tx_slots=self.mac_data.get_bcn_slotmap(mac_tdma_cfg.FRAME_SPEC_SF_ORDER),
            # extended fields:
            station_id=socket.gethostname().encode(),
            geoloc=getattr(self, "gps_gprmc", b""), #TODO: extract lat/lon from gprmc
            )
        tx_args = (abs_time, phy_cfg.tx_freq, bytes(frame)) # tx time, freq and data
        farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_TRANSMIT, tx_args), "SX127xSpiAhsm")


    @staticmethod
    def tx_from_txq(self, abs_time):
        """Creates a frame, inserts the payload that is next in the queue
        and dispatches the frame to the PHY for transmission.
        Assumes caller checked that the queue is not empty.
        """
        frame = self.build_mac_frame(self)
        frame.data = self.mac_txq.pop()
        tx_args = (abs_time, phy_cfg.tx_freq, bytes(frame)) # tx time, freq and data
        farc.Framework.post_by_name(farc.Event(farc.Signal.PHY_TRANSMIT, tx_args), "SX127xSpiAhsm")


    @staticmethod
    def ngbr_hears_me(self,):
        """Returns True if at least one neighbor lists this node
        in its extended beacon neighbor report;
        proving two-way transmission has taken place.
        """
        ngbr_ebcns = self.mac_data.get_ebcns()
        for ngbr, ebcn in ngbr_ebcns.items():
            if ebcn.valid:
                ebcn = ebcn.value
                for n in ebcn.ngbrs:
                    if n[0] == self.saddr:
                        return True
        return False


    @staticmethod
    def pick_bcn_slot(self,):
        """Returns one slot in the Sframe for beacon transmission.
        The initial choice is a piece of static psuedo-random data
        (a byte from the node's public key) so that the beacon slot
        might remain the same from one run to the next.
        However, if any neighbor beacons have been received,
        the initial choice may be overridden to avoid collision.
        """
        # The initial value for this node's beacon slot.
        bcn_slot = (mac_identity['pub_key'][0] << 8 | mac_identity['pub_key'][1]) \
                   % (2 ** self.sf_order)

        # Increment the intial value while there is a collision with neighboring beacons
        bcn_slotmap = self.mac_data.get_bcn_slotmap(mac_tdma_cfg.FRAME_SPEC_SF_ORDER)
        while bcn_slotmap[ bcn_slot // 8 ] & (1 << (bcn_slot % 8)):
            bcn_slot += 1

        return bcn_slot

