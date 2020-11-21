#!/usr/bin/env python3
"""
Copyright 2020 Dean Hall.  See LICENSE for details.
"""

import collections
import logging
import time

import farc

from . import phy_sx127x


class PhySX127xAhsm(farc.Ahsm):
    """The PHY layer state machine that automates the behavior
    of the Semtech SX127x family of radio transceivers.
    """
    # Values for enqueue_for_tx()'s tm_to_tx argument.
    ENQ_TX_NOW = 0  # Use normally for "transmit now"
    ENQ_TX_IMMEDIATELY = -1 # Use sparingly to jump the queue

 
    def __init__(self, lstn_by_dflt=True):
        """Listen by default means the radio enters
        continuous-rx mode when it is not doing anything else.
        If this is false, the radio enters sleep mode
        when it is not doing anything else.
        """
        super().__init__()
        self.sx127x = phy_sx127x.PhySX127x()
        self._lstn_by_dflt = lstn_by_dflt


#### Public interface

    def enqueue_for_tx(self, frame, tm_to_tx, tx_stngs):
        """Enqueues the given frame bytes for transmit
        at the given time with the given settings.
        """
        assert type(frame) is bytes

        tx_data = (frame, tm_to_tx, tx_stngs)

        # IMMEDIATELY means this frame jumps to the front of the line
        # put it in the immediate queue (which goes before the tm_queue)
        if tm_to_tx == PhySX127xAhsm.ENQ_TX_IMMEDIATELY:
            self.im_queue.append(tx_data)
        else:
            # NOW means assume a transmit time of now and
            # pool this frame with other scheduled frames
            if tm_to_tx == PhySX127xAhsm.ENQ_TX_NOW:
                tm_to_tx = now = farc.Framework._event_loop.time()

            # Ensure this tx time doesn't overwrite an existing one
            # by adding one microsecond if there is a duplicate.
            # This results in FIFO for frames scheduled at the same time.
            while tm_to_tx in self.tm_queue:
                tm_to_tx += 0.000_001
            self.tm_queue[tm_to_tx] = tx_data

        # There is now something to transmit,
        # so break out of the normal state (rx-cont or sleep)
        # by signaling the state machine to reschedule
        self.post_fifo(self._evt_reschedule)


    def start_stack(self, farc_prio):
        """This is the bottom of the stack,
        so just start this Ahsm
        """
        self.start(farc_prio)


#### Private interface

    def _dio_isr_clbk(self, dio):
        """A callback that is given to phy_sx127x
        for when a DIO pin event occurs.
        This procedure posts a farc Event to this state machine
        corresponding to the DIO pin that transitioned.
        The pin edge's arrival time is the value of the Event.
        """
        now = farc.Framework._event_loop.time()
        self.post_fifo(farc.Event(self._dio_sig_lut[dio], now))


#### State machine

    @farc.Hsm.state
    def _initial(self, event):
        """State machine intialization
        """
        # Self-signaling
        farc.Signal.register("_ALWAYS")
        farc.Signal.register("_RESCHEDULE")

        # DIO Signal table (DO NOT CHANGE ORDER)
        # This table is dual maintenance with  phy_sx127x.PhySX127x.DIO_*
        self._dio_sig_lut = (
            farc.Signal.register("_DIO_MODE_RDY"),
            farc.Signal.register("_DIO_CAD_DETECTED"),
            farc.Signal.register("_DIO_CAD_DONE"),
            farc.Signal.register("_DIO_FHSS_CHG_CHNL"),
            farc.Signal.register("_DIO_RX_TMOUT"),
            farc.Signal.register("_DIO_RX_DONE"),
            farc.Signal.register("_DIO_CLK_OUT"),
            farc.Signal.register("_DIO_PLL_LOCK"),
            farc.Signal.register("_DIO_VALID_HDR"),
            farc.Signal.register("_DIO_TX_DONE"),
            farc.Signal.register("_DIO_PAYLD_CRC_ERR"),
        )

        # Self-signaling events
        self._evt_always = farc.Event(farc.Signal._ALWAYS, None)
        self._evt_reschedule = farc.Event(farc.Signal._RESCHEDULE, None)

        # Two time events
        self.tmout_evt = farc.TimeEvent("_PHY_TMOUT")
        self.prdc_evt = farc.TimeEvent("_PHY_PRDC")

        return self.tran(self._initializing)


    @farc.Hsm.state
    def _initializing(self, event):
        """Application initialization
        Instantiates, opens and verifies the SPI driver.
        Sets default application values.
        Transitions to the _setting state if the SPI Comms
        and SX127x are good; otherwise, remains in this state
        and periodically retries opening the SX127x.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            self.tmout_evt.post_in(self, 0.0)

            # Init data
            # We actually use two queues:
            # One queue for frames that sort by tx time
            self.tm_queue = {}
            # Another queue for frames the need to be sent immediately
            self.im_queue = []
            return self.handled(event)

        elif sig == farc.Signal._PHY_TMOUT:
            if self.sx127x.open(self._dio_isr_clbk):
                # Settings that differ from reset
                self.sx127x.set_fld("FLD_RDO_LORA_MODE", 1)
                self.sx127x.set_fld("FLD_RDO_FREQ", 432550000)
                self.sx127x.set_fld("FLD_RDO_MAX_PWR", 7)
                self.sx127x.set_fld("FLD_RDO_PA_BOOST", 1)
                self.sx127x.set_fld("FLD_LORA_BW", phy_sx127x.PhySX127x.STNG_LORA_BW_250K)
                self.sx127x.set_fld("FLD_LORA_SF", phy_sx127x.PhySX127x.STNG_LORA_SF_128_CPS)
                self.sx127x.set_fld("FLD_LORA_CR", phy_sx127x.PhySX127x.STNG_LORA_CR_4TO6)
                self.sx127x.set_fld("FLD_LORA_CRC_EN", 1)
                self.sx127x.set_fld("FLD_LORA_SYNC_WORD", 0x48) # FIXME: magic number
                return self.tran(self._setting)

            logging.info("_initializing: no SX127x or SPI")
            self.tmout_evt.post_in(self, 1.0)
            return self.handled(event)

        elif sig == farc.Signal.EXIT:
            self.tmout_evt.disarm()
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _setting(self, event):
        """Writes any outstanding settings and always
        transitions to _txing, _sleeping or _lstning
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            # 1a) If any outstanding settings require sleep mode,
            # change to sleep mode.  Await DIO_MODE_RDY.
            self.need_sleep = self.sx127x.stngs_require_sleep()
            if self.need_sleep:
                self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_SLEEP, True)
                return self.handled(event)

            # 1b) If sleep mode is not needed, jump to 4
            self.post_fifo(self._evt_always)
            return self.handled(event)

        elif sig == farc.Signal._DIO_MODE_RDY:
            # 2) If outstanding settings require sleep mode,
            # write the sleep mode settings, clear the need-sleep flag and
            # change to standby mode and await DIO_MODE_RDY.
            if self.need_sleep:
                self.need_sleep = False
                self.sx127x.write_sleep_stngs()
                self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_STBY, True)
                return self.handled(event)

            # 3) Arrived in standby mode, continue to 4
            self.post_fifo(self._evt_always)
            return self.handled(event)

        elif sig == farc.Signal._ALWAYS:
            # 4) Apply settings and transition to one of three states
            if self._frame_ready_for_tx():
                self.sx127x.write_stngs(False)
                return self.tran(self._txing)

            elif self._lstn_by_dflt:
                self.sx127x.write_stngs(True)
                return self.tran(self._lstning)

            else:
                return self.tran(self._sleeping)

        return self.super(self.top)


    @farc.Hsm.state
    def _lstning(self, event):
        """Puts the modem into receive mode.
        Transitions to _rxing if a valid header is received.
        An Update signal causes transition to _setting
        to reach a different state such as _txing can.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            # Transmit settings
            self.sx127x.set_fld("FLD_RDO_DIO0", 0) # _DIO_RX_DONE
            self.sx127x.set_fld("FLD_RDO_DIO1", 0) # _DIO_RX_TMOUT
            self.sx127x.set_fld("FLD_RDO_DIO3", 1) # _DIO_VALID_HDR
            self.sx127x.write_stngs(True)
            self.sx127x.write_lora_irq_mask(
                phy_sx127x.PhySX127x.IRQ_FLAGS_ALL,
                phy_sx127x.PhySX127x.IRQ_FLAGS_RXDONE |
                phy_sx127x.PhySX127x.IRQ_FLAGS_PAYLDCRCERROR |
                phy_sx127x.PhySX127x.IRQ_FLAGS_VALIDHEADER
            )
            self.sx127x.write_lora_irq_flags(
                phy_sx127x.PhySX127x.IRQ_FLAGS_RXDONE |
                phy_sx127x.PhySX127x.IRQ_FLAGS_PAYLDCRCERROR |
                phy_sx127x.PhySX127x.IRQ_FLAGS_VALIDHEADER
            )
            self.sx127x.write_fifo_ptr(0x00)

            # Start periodic event
            self.prdc_evt.post_every(self, 0.100)  # 100ms

            # Enable RF receiver
            # TODO: option for timed rx
            self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_RXCONT)
            return self.handled(event)

        elif sig == farc.Signal._DIO_RX_TMOUT:
            # TODO: log pkt stats
            return self.tran(self._setting)

        elif sig == farc.Signal._PHY_PRDC:
            self.sx127x.updt_rng()
            return self.handled(event)

        elif sig == farc.Signal._RESCHEDULE:
            return self.tran(self._setting)

        elif sig == farc.Signal._DIO_VALID_HDR:
            self._rxd_hdr_time = event.value
            return self.tran(self._rxing)

        elif sig == farc.Signal.EXIT:
            # Stop periodic event on exit
            self.prdc_evt.disarm()
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _rxing(self, event):
        """Protects a reception in progress.
        Transitions to _setting after frame is received.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            # Enable only the RX interrupts (disable all others)
            self.sx127x.write_lora_irq_mask(
                phy_sx127x.PhySX127x.IRQ_FLAGS_ALL,  # Disable these
                phy_sx127x.PhySX127x.IRQ_FLAGS_RXTIMEOUT # Enable these
                | phy_sx127x.PhySX127x.IRQ_FLAGS_RXDONE
                | phy_sx127x.PhySX127x.IRQ_FLAGS_PAYLDCRCERROR
                | phy_sx127x.PhySX127x.IRQ_FLAGS_VALIDHEADER)

            # Receive settings
            self.sx127x.set_fld("FLD_RDO_DIO0", 0) # _DIO_RX_DONE
            self.sx127x.set_fld("FLD_RDO_DIO1", 0) # _DIO_RX_TMOUT
            self.sx127x.set_fld("FLD_RDO_DIO3", 1) # _DIO_VALID_HDR

            self.sx127x.set_lora_rx_fifo(self.dflt_modem_stngs["modulation_stngs"]["rx_base_ptr"])
            self.sx127x.set_lora_rx_freq(self.rx_freq)

            return self.handled(event)

        elif sig == farc.Signal._DIO_PAYLD_CRC_ERR:
            # TODO: log dio rx payld crc err
            # TODO: incr lnk_data stats crc err cnt
            return self.tran(self._setting)

        elif sig == farc.Signal._DIO_RX_TMOUT:
            # TODO: log dio rx tmout
            # TODO: incr lnk_data stats rx tmout
            return self.tran(self._setting)

        elif sig == farc.Signal._DIO_RX_DONE:
            frame_bytes, rssi, snr = self.sx127x.read_lora_rxd()
            # TODO: check sx127x for any rx errors
            if True: # no errors
                # TODO: log rx done
                # TODO: incr lnk_data stats rx done
                # TODO: self.nlh_rx_clbk(frame_bytes, self._rxd_hdr_time, rssi, snr)
                pass
            else: # errors
                # TODO: log err_type
                # TODO: incr lnk_data stats rx err
                pass
            return self.tran(self._setting)

        return self.super(self.top)


    @farc.Hsm.state
    def _sleeping(self, event):
        """Puts the modem into sleep mode.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_SLEEP, False)
            # TODO: start a timer to exit sleep mode
            # self.tmout_evt.post_in(self, 1.0)
            return self.handled(event)

        elif sig == farc.Signal._PHY_TMOUT:
            # Change modes and await DIO_MODE_RDY
            self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_STBY, True)
            return self.handled(event)

        elif sig == farc.Signal._DIO_MODE_RDY:
            return self.tran(self._setting)

        elif sig == farc.Signal._RESCHEDULE:
            return self.tran(self._setting)

        return self.super(self.top)


    @farc.Hsm.state
    def _txing(self, event):
        """Prepares for transmission, transmits,
        awaits DIO_TX_DONE event from radio,
        then transitions to the _setting state.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            tx_data = self._get_next_tx_data()
            assert bool(tx_data), "No tx data!  How did we get here?"
            frame, tm_to_tx, tx_stngs = tx_data

            # TODO: apply tx_stngs
            # TODO: microsleep until tm_to_tx

            # Enable radio's DIO_TX_DONE pin and interrupt
            self.sx127x.set_fld("FLD_RDO_DIO0", 1)
            self.sx127x.write_stng("FLD_RDO_DIO0")
            self.sx127x.write_lora_irq_mask(
                phy_sx127x.PhySX127x.IRQ_FLAGS_ALL,  # disable these
                phy_sx127x.PhySX127x.IRQ_FLAGS_TXDONE)  #enable these

            # Write frame into radio's FIFO
            self.sx127x.write_fifo_ptr(0x00)
            self.sx127x.write_fifo(frame)

            # Start transmission and await DIO_TX_DONE
            self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_TX, False)
            return self.handled(event)

        elif sig == farc.Signal._DIO_TX_DONE:
            return self.tran(self._setting)

        return self.super(self.top)


#### Private methods

    def _frame_ready_for_tx(self,):
        """Returns True if there is a frame in the queues
        that is ready for transmit soon.
        Where "soon" means we don't have enough time to sleep
        between now and the transmit time.
        """
        TX_SOON_MARGIN = 0.100 # 100ms TODO: improve this arbitrary choice

        frame_ready = False

        # Return True if there is anything in the immediate queue
        if len(self.im_queue) > 0:
            frame_ready = True

        # Return True if there is something in the time queue
        # that needs to be transmitted soon
        elif self.tm_queue:
            now = farc.Framework._event_loop.time()
            tx_tm = min(self.tm_queue.keys())
            if tx_tm - now < TX_SOON_MARGIN:
                frame_ready = True
        return frame_ready


    def _get_next_tx_data(self,):
        """Returns the tx_data from the queue
        to use in the next transmission
        """
        tx_data = None

        if self.im_queue:
            tx_data = self.im_queue.pop()

        elif self.tm_queue:
            tx_tm = min(self.tm_queue.keys())
            tx_data = self.tm_queue[tx_tm]

        return tx_data
