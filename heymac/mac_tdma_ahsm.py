#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.

MAC (data link layer) (layer 2) State Machine for protocol operations
- listens for PPS signal and RX packet times to synchronize to a network
- selects an appropriate Timeslot to periodically transmit a beacon frame
- maintains a schedule of transmit and receive Timeslots
- maintains a list of neighbors with link quality stats
"""


import logging, hashlib, math

import pq

import mac_cmds, mac_discipline, mac_frame
import mac_cfg, phy_cfg, cfg


# Turn user JSON config files into Python dicts
mac_identity = cfg.get_from_json("mac_identity.json")
# Convert hex bytes to bytearray since JSON can't do binary strings
mac_identity['pub_key'] = bytearray.fromhex(mac_identity['pub_key'])


class HeyMacAhsm(pq.Ahsm):

    @staticmethod
    def initial(me, event):
        """Pseudostate: HeyMacAhsm:initial
        """
        # Incoming signals
        pq.Framework.subscribe("PHY_GPS_PPS", me)
        pq.Framework.subscribe("PHY_RXD_DATA", me)
        pq.Framework.subscribe("GPS_NMEA", me) # from phy_uart_ahsm.py

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
        logging.info("bcn_slot (%d / %d)" % (me.bcn_slot, mac_cfg.TSLOTS_PER_SFRAME))

        me.time_of_last_pps = None
        me.time_of_last_rxd_bcn = None
        me.dscpln = mac_discipline.HeyMacDiscipline()

        # Neighbor info
        me.bcn_ngbr_slotmap = bytearray(mac_cfg.TSLOTS_PER_SFRAME // 8)

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
            time_of_pps = event.value
            me.dscpln.update_pps(time_of_pps, me.time_of_last_pps)
            me.time_of_last_pps = time_of_pps
            me.tslots_since_last_pps = 0
            return me.handled(me, event)

        elif sig == pq.Signal.PHY_RXD_DATA:
            rx_time, payld, rssi, snr = event.value
            me.on_rxd_frame(me, rx_time, payld, rssi, snr)
            return me.handled(me, event)

        elif sig == pq.Signal.GPS_NMEA:
            me.gps_gprmc = event.value
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
            logging.info("LISTENING")
            value = (-1, phy_cfg.rx_freq) # rx continuously on the rx_freq
            pq.Framework.post(pq.Event(pq.Signal.RECEIVE, value), "SX127xSpiAhsm")
            listen_secs = N_SFRAMES_TO_LISTEN * mac_cfg.TSLOTS_PER_SFRAME / mac_cfg.TSLOTS_PER_SEC
            me.tm_evt.postIn(me, listen_secs)
            return me.handled(me, event)

        elif sig == pq.Signal.TM_EVT_TMOUT: # timer has expired
            # If two PPS have been received, transfer to scheduling state
            if me.time_of_last_pps:
                return me.tran(me, me.scheduling)
            else:
                logging.info("remain listening")
                listen_secs = N_SFRAMES_TO_LISTEN * mac_cfg.TSLOTS_PER_SFRAME / mac_cfg.TSLOTS_PER_SEC
                me.tm_evt.postIn(me, listen_secs)
                return me.handled(me, event)
 
        elif sig == pq.Signal.PHY_RXD_DATA:
            # handle received frame
            rx_time, payld, rssi, snr = event.value
            me.on_rxd_frame(me, rx_time, payld, rssi, snr)

            # rx continuously again
            value = (-1, phy_cfg.rx_freq)
            pq.Framework.post(pq.Event(pq.Signal.RECEIVE, value), "SX127xSpiAhsm")
            return me.handled(me, event)

        # This handler is for debug-print only and may be removed
        elif sig == pq.Signal.PHY_GPS_PPS:
            logging.info("pps            %f", event.value)
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
            logging.info("EXITING")
            return me.handled(me, event)
        
        return me.super(me, me.top)


#### End State Machines

    @staticmethod
    def scheduling_and_entry(self,):
        """Handler for the Scheduling state entry event.
        Uses timing discipline data to set a time event for the next Tslot.
        """
        logging.info("SCHEDULING")

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
            logging.info("tm_of_last_pps %f", self.time_of_last_pps)
            logging.info("bcn_tslot (pps)%f", self.next_tslot)
            self.tx_bcn(self, self.next_tslot)

        # TODO: send the top pkt in the tx que

        # Listen during every Tslot
        else:
            value = (self.next_tslot, phy_cfg.rx_freq) # rx time and freq
            pq.Framework.post(pq.Event(pq.Signal.RECEIVE, value), "SX127xSpiAhsm")

        # Count this Tslot and set the TimeEvent to expire at the next Prep Time
        self._post_time_event_for_next_tslot(self)


    @staticmethod
    def _post_time_event_for_next_tslot(self,):
        """Sets the TimeEvent to expire at the next Prep Time.
        When calculating next_tslot it is important to reference to the
        source of absolute time (time of most recent PPS) so that there is
        less accumulated error.
        """
        TSLOT_PREP_TIME = 0.020 # secs.
        self.next_tslot = self.time_of_last_pps + (1 + self.tslots_since_last_pps) * self.dscpln.get_time_per_tslot()
        self.tm_evt.postAt(self, self.next_tslot - mac_cfg.TSLOT_PREP_TIME)


    @staticmethod
    def build_mac_frame(self, seq=0):
        """Returns a generic HeyMac V1 frame with the given sequence number
        """
        frame = mac_frame.HeyMacFrame(fctl=mac_frame.FCTL_TYPE_MAC
            | mac_frame.FCTL_LENCODE_BIT
            | mac_frame.FCTL_SADDR_MODE_64BIT)
        frame.saddr = self.saddr
        frame.seq = seq
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
        logging.info(
            "rx_time        %f\tRXD %d bytes, rssi=%d dBm, snr=%.3f dB\t%s",
            rx_time, len(payld), rssi, snr, repr(f))

        if isinstance(f.data, mac_cmds.HeyMacCmdBeacon):
            self.on_rxd_bcn(self, rx_time, f.data, rssi, snr)
        else:
            logging.warning("rxd pkt is not a bcn")


    @staticmethod
    def on_rxd_bcn(self, rx_time, bcn_frame, rssi, snr):
        """Handles reception of a beacon frame.
        """
        self.dscpln.update_bcn(rx_time, self.time_of_last_rxd_bcn)
        self.time_of_last_rxd_bcn = rx_time
        self.tslots_since_last_bcn = 0

        # Adopt the larger ASN
        if bcn_frame.asn > self.asn:
            self.asn = bcn_frame.asn

        # TEMPORARY:
        assert bcn_frame.sframe_nTslots == mac_cfg.TSLOTS_PER_SFRAME, "Ngbr's Sframe cfg is incompatible"

        # TEMPORARY: Update Ngbr beacon slots
        # (this is an incomplete method, it does not allow the slot to be cleared if ngbr is silent)
        ngbr_bcnslot = self.asn % mac_cfg.TSLOTS_PER_SFRAME
        self.bcn_ngbr_slotmap[ ngbr_bcnslot // 8 ] |= (1 << (ngbr_bcnslot % 8))

        # TODO: add to ngbr data


    @staticmethod
    def tx_bcn(self, abs_time):
        """Builds a HeyMac V1 Beacon and passes it to the PHY for transmit.
        """
        frame = self.build_mac_frame(self, self.bcn_seq)
        bcn = mac_cmds.HeyMacCmdBeacon(
            dscpln=0,
            sframe_nTslots=mac_cfg.TSLOTS_PER_SFRAME,
            asn=self.asn, 
            caps=0,
            flags=0,
            callsign=mac_cfg.CALLSIGN,
            geoloc=self.gps_gprmc, #TODO: extract lat/lon from gprmc
            )
        bcn.ngbr_slotmap = tuple(self.bcn_ngbr_slotmap)
        frame.data = bcn
        tx_args = (abs_time, phy_cfg.tx_freq, bytes(frame)) # tx time, freq and data
        pq.Framework.post(pq.Event(pq.Signal.TRANSMIT, tx_args), "SX127xSpiAhsm")
        self.bcn_seq += 1
