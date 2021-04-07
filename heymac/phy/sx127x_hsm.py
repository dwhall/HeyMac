"""
Copyright 2020 Dean Hall.  See LICENSE for details.
"""

import logging
import time

import farc

from .sx127x import SX127x


class SX127xHsm(farc.Ahsm):
    """The physical layer (PHY) state machine for a Semtech SX127x device.

    Automates the behavior of the Semtech SX127x family of radio transceivers.
    For now, all behavior and operations are for LoRa mode.
    """
    # Special time values to use when posting an action
    TM_NOW = 0          # Use normally for "do it now"
    TM_IMMEDIATE = -1   # Use sparingly to jump the queue


    def __init__(self, lstn_by_dflt):
        """Class intialization

        Listen by default means the radio enters
        continuous-rx mode when it is not doing anything else.
        If lstn_by_dflt is False, the radio enters sleep mode
        when it is not doing anything else.
        """
        super().__init__()
        self._sx127x = SX127x()
        self._lstn_by_dflt = lstn_by_dflt
        self._base_stngs = {}
        self._rx_stngs = {}
        self._tx_stngs = {}


    def get_stngs(self):
        """Returns the current settings"""
        return self._sx127x.get_applied_stngs()


    def post_rx_action(self, rx_time, rx_stngs, rx_durxn, rx_clbk):
        """Posts the _PHY_RQST event to this state machine
        with the container-ized arguments as the value.
        """
        assert not self._lstn_by_dflt, \
            """post_rx_action() should not be used when the PHY is
            listen-by-default.  Use set_dflt_rx_clbk() once, instead."""
        # Convert NOW to an actual time
        if rx_time == SX127xHsm.TM_NOW:
            rx_time = farc.Framework._event_loop.time()
        # The order MUST begin: (action, stngs, ...)
        rx_action = ("rx", rx_stngs, rx_durxn, rx_clbk)
        self.post_fifo(farc.Event(farc.Signal._PHY_RQST, (rx_time, rx_action)))


    def post_tx_action(self, tx_time, tx_stngs, tx_bytes):
        """Posts the _PHY_RQST event to this state machine
        with the container-ized arguments as the value.
        """
        assert type(tx_bytes) is bytes
        # Convert NOW to an actual time
        if tx_time == SX127xHsm.TM_NOW:
            tx_time = farc.Framework._event_loop.time()
        # The order MUST begin: (action, stngs, ...)
        tx_action = ("tx", tx_stngs, tx_bytes)
        self.post_fifo(farc.Event(farc.Signal._PHY_RQST, (tx_time, tx_action)))


    def set_dflt_rx_clbk(self, rx_clbk):
        """Stores the default RX callback for the PHY.

        The default RX callback is used when this state machine is
        initialized with listen-by-default set to True.
        This state machine calls the default RX callback
        when a frame is received and there are no reception errors.
        """
        assert self._lstn_by_dflt, \
            """set_dflt_rx_clbk() should not be used when the PHY is
            sleep-by-default.  Pass a callback in post_rx_action() instead.
            """
        self._dflt_rx_clbk = rx_clbk


    def update_base_stngs(self, stngs):
        """Stores the base settings for the PHY.

        This must be called before start() so the settings
        can be written to the device during initilizing.
        Base settings are the ones that are usually the
        same throughout operation and do not vary
        during TX, RX or any other action.
        """
        self._base_stngs.update(stngs)


# State machine


    @farc.Hsm.state
    def _initial(self, event):
        """Pseudostate: _initial

        State machine framework initialization
        """
        # Self-signaling
        farc.Signal.register("_ALWAYS")
        farc.Signal.register("_PHY_RQST")

        # DIO Signal table (DO NOT CHANGE ORDER)
        # This table is dual maintenance with sx127x.SX127x.DIO_*
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

        # Time events
        self.tmout_evt = farc.TimeEvent("_PHY_TMOUT")
        self.prdc_evt = farc.TimeEvent("_PHY_PRDC")

        return self.tran(self._initializing)


    @farc.Hsm.state
    def _initializing(self, event):
        """"State: _initializing

        Application initialization.
        Opens and verifies the SPI driver.
        Sets default application values.
        Transitions to the _scheduling state if the SPI Comms
        and SX127x are good; otherwise, remains in this state
        and periodically retries opening the SX127x.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._initializing")
            self.tmout_evt.post_in(self, 0.0)

            # Init data
            # We use two queues for a hybrid time-sorted queue:
            # One for frames that sort by time.
            # It's actually a dict object where the keys are the time value.
            self._tm_queue = {}
            # Another for frames that need to be sent immediately.
            # This should be used sparingly.
            self._im_queue = []
            return self.handled(event)

        elif sig == farc.Signal._PHY_TMOUT:
            if self._sx127x.open(self._dio_isr_clbk):
                assert len(self._base_stngs) > 0, \
                    "Base settings must be set before initializing"
                self._sx127x.set_flds(self._base_stngs)
                self._sx127x.write_stngs(False)
                return self.tran(self._scheduling)

            logging.warning("_initializing: no SX127x or SPI")
            self.tmout_evt.post_in(self, 1.0)
            return self.handled(event)

        elif sig == farc.Signal.EXIT:
            self.tmout_evt.disarm()
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _scheduling(self, event):
        """"State: _scheduling

        Writes any outstanding settings and always
        transitions to _txing, _sleeping or _listening
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._scheduling")
            # TODO: remove unecessary read once sm design is proven
            assert SX127x.OPMODE_STBY == self._sx127x.read_opmode()
            self.post_fifo(farc.Event(farc.Signal._ALWAYS, None))
            return self.handled(event)

        elif sig == farc.Signal._ALWAYS:
            # If the next action is soon, go to its state
            next_action = self._top_soon_action()
            self._default_action = not bool(next_action)
            if next_action:
                _, action = next_action
                if action[0] == "rx":
                    st = self._listening
                elif action[0] == "tx":
                    st = self._txing
                else:
                    # Placeholder for CAD, sleep
                    assert False, "Got here by accident"

            # Otherwise, go to the default
            elif self._lstn_by_dflt:
                st = self._listening
            else:
                st = self._sleeping

            return self.tran(st)

        elif sig == farc.Signal._PHY_RQST:
            tm, action = event.value
            self._enqueue_action(tm, action)
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _lingering(self, event):
        """"State: _scheduling

        This state is for shared behavior
        between the _listening and _sleeping states.
        On entry, optionally starts a timer for when
        to exit to go handle the next action.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._lingering")
            return self.handled(event)

        elif sig == farc.Signal._PHY_RQST:
            tm, action = event.value
            self._enqueue_action(tm, action)
            # If lingering because of default action
            # transition to scheduling
            if self._default_action:
                return self.tran(self._scheduling)
            # If lingering because of intentional action
            # remain in current state
            return self.handled(event)

        elif sig == farc.Signal._PHY_TMOUT:
            return self.tran(self._scheduling)

        elif sig == farc.Signal.EXIT:
            self.tmout_evt.disarm()
            # Changing modes from rx or sleep to STBY is
            # "near instantaneous" per SX127x datasheet
            # so don't bother awaiting a _DIO_MODE_RDY
            self._sx127x.write_opmode(SX127x.OPMODE_STBY, False)
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _listening(self, event):
        """"State: _lingering:_listening

        Puts the device into receive mode
        either because of a receive action or listen-by-default.
        Transitions to _rxing if a valid header is received.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._lingering._listening")
            action = self._pop_soon_action()
            stngs = self._base_stngs
            if action:
                rx_time, rx_action = action
                (action_str, rx_stngs, rx_durxn, rx_clbk) = rx_action
                assert action_str == "rx"
                self._rx_clbk = rx_clbk
                stngs.update(rx_stngs)
            else:
                self._rx_clbk = self._dflt_rx_clbk

            # Combine and write RX settings
            stngs.update({"FLD_RDO_DIO0": 0,    # _DIO_RX_DONE
                          "FLD_RDO_DIO1": 0,    # _DIO_RX_TMOUT
                          "FLD_RDO_DIO3": 1})   # _DIO_VALID_HDR
            self._sx127x.set_flds(stngs)
            self._sx127x.write_stngs(True)

            # Prep interrupts for RX
            self._sx127x.write_lora_irq_mask(
                    SX127x.IRQ_FLAGS_ALL,
                    SX127x.IRQ_FLAGS_RXDONE |
                    SX127x.IRQ_FLAGS_PAYLDCRCERROR |
                    SX127x.IRQ_FLAGS_VALIDHEADER)
            self._sx127x.write_lora_irq_flags(
                    SX127x.IRQ_FLAGS_RXDONE |
                    SX127x.IRQ_FLAGS_PAYLDCRCERROR |
                    SX127x.IRQ_FLAGS_VALIDHEADER)
            self._sx127x.write_fifo_ptr(0x00)

            # Start periodic event for update_rng()
            self.prdc_evt.post_every(self, 0.100)  # 100ms

            # No action means listen-by-default; receive-continuosly
            if not action:
                self._sx127x.write_opmode(SX127x.OPMODE_RXCONT, False)

            # An explicit action means do a receive-once
            else:
                # Perform a short blocking sleep until rx_time
                # to obtain more accurate rx execution time on Linux.
                now = farc.Framework._event_loop.time()
                tiny_sleep = rx_time - now
                assert tiny_sleep > 0.0, \
                    "didn't beat action time, need to increase _TM_SVC_MARGIN"
                if tiny_sleep > SX127xHsm._TM_BLOCKING_MAX:
                    tiny_sleep = SX127xHsm._TM_BLOCKING_MAX
                if tiny_sleep > SX127xHsm._TM_BLOCKING_MIN:
                    time.sleep(tiny_sleep)
                self._sx127x.write_opmode(SX127x.OPMODE_RXONCE, False)
                # Start the rx duration timer
                if rx_durxn > 0:
                    self.tmout_evt.post_in(self, rx_durxn)
            return self.handled(event)

        elif sig == farc.Signal._PHY_PRDC:
            self._sx127x.updt_rng()
            return self.handled(event)

        elif sig == farc.Signal._DIO_VALID_HDR:
            self._rxd_hdr_time = event.value
            return self.tran(self._rxing)

        elif sig == farc.Signal._DIO_PAYLD_CRC_ERR:
            logging.info("PHY:_listening@_DIO_PAYLD_CRC_ERR")
            # TODO: incr phy_data stats crc err cnt
            return self.tran(self._scheduling)

        elif sig == farc.Signal._DIO_RX_TMOUT:
            logging.info("PHY:_listening@_DIO_RX_TMOUT")
            # TODO: incr phy_data stats rx tmout
            return self.tran(self._scheduling)

        elif sig == farc.Signal.EXIT:
            self.prdc_evt.disarm()
            return self.handled(event)

        return self.super(self._lingering)


    @farc.Hsm.state
    def _rxing(self, event):
        """"State: _lingering:_listening:_rxing

        Continues a reception in progress.
        Protects reception by NOT transitioning upon a _PHY_RQST event.
        Transitions to _scheduling after reception ends.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._rxing")
            return self.handled(event)

        elif sig == farc.Signal._DIO_RX_DONE:
            self._on_lora_rx_done()
            return self.tran(self._scheduling)

        elif sig == farc.Signal._PHY_RQST:
            # Overrides _lingering's _PHY_RQST handler because we want to
            # remain in this state even if we were listening-by-default
            tm, action = event.value
            self._enqueue_action(tm, action)
            return self.handled(event)

        return self.super(self._listening)


    @farc.Hsm.state
    def _sleeping(self, event):
        """"State: _lingering:_sleeping

        Puts the device into sleep mode.
        Timer and timeout handling is performed
        by the parent state, _lingering()
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._lingering._sleeping")
            self._sx127x.write_opmode(SX127x.OPMODE_SLEEP, False)
            return self.handled(event)

        return self.super(self._lingering)


    @farc.Hsm.state
    def _txing(self, event):
        """"State: _txing

        Prepares for transmission, transmits,
        awaits DIO_TX_DONE event from radio,
        then transitions to the _scheduling state.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._txing")
            action = self._pop_soon_action()
            stngs = self._base_stngs
            assert action is not None, "Mutation between top() and pop()"
            (tx_time, tx_action) = action
            assert tx_action[0] == "tx", "Mutation between top() and pop()"
            (_, tx_stngs, tx_bytes) = tx_action
            stngs.update(tx_stngs)

            # Write TX settings from higher layer and
            # one setting needed for this PHY operation
            stngs.update({"FLD_RDO_DIO0": 1})   # _DIO_TX_DONE
            self._sx127x.set_flds(stngs)
            self._sx127x.write_stngs(False)

            # Prep interrupts for TX
            self._sx127x.write_lora_irq_mask(
                    SX127x.IRQ_FLAGS_ALL,     # disable these
                    SX127x.IRQ_FLAGS_TXDONE)  # enable these

            # Write payload into radio's FIFO
            self._sx127x.write_fifo_ptr(0x00)
            self._sx127x.write_fifo(tx_bytes)
            self._sx127x.write_lora_payld_len(len(tx_bytes))

            # Blocking sleep until tx_time (assuming a short amount)
            now = farc.Framework._event_loop.time()
            tiny_sleep = tx_time - now
            if tiny_sleep > SX127xHsm._TM_BLOCKING_MAX:
                tiny_sleep = SX127xHsm._TM_BLOCKING_MAX
            if tiny_sleep > 0.001:
                time.sleep(tiny_sleep)

            # Start software timer for backstop
            self.tmout_evt.post_in(self, 1.0)   # TODO: calc soft timeout delta

            # Start transmission and await DIO_TX_DONE
            self._sx127x.write_opmode(SX127x.OPMODE_TX, False)
            return self.handled(event)

        elif sig == farc.Signal._DIO_TX_DONE:
            # TODO: phy stats TX_DONE
            return self.tran(self._scheduling)

        elif sig == farc.Signal._PHY_RQST:
            tm, action = event.value
            self._enqueue_action(tm, action)
            return self.handled(event)

        elif sig == farc.Signal._PHY_TMOUT:
            logging.warning("PHY._txing@_PHY_TMOUT")
            if self._sx127x.in_sim_mode():
                # Sim-radio will never emit DIO events
                # so go straight to _scheduling
                return self.tran(self._scheduling)
            else:
                # SX127x takes time to change modes from TX to STBY.
                # Use DIO5/ModeReady here so we don't transition
                # to _scheduling and try to do stuff before the
                # chip is in STBY mode.  Await _DIO_MODE_RDY.
                self._sx127x.write_opmode(SX127x.OPMODE_STBY, True)
                return self.handled(event)

        elif sig == farc.Signal._DIO_MODE_RDY:
            return self.tran(self._scheduling)

        elif sig == farc.Signal.EXIT:
            self.tmout_evt.disarm()
            return self.handled(event)

        return self.super(self.top)


# Private


    # The margin within which the Hsm will transition to
    # the action's state if there is an entry in the action queue;
    # otherwise, transitions to the default state, listening or sleeping.
    _TM_SOON = 0.040

    # The amount of time it takes to get from the _lingering state
    # through _scheduling and to the next action's state.
    # This is used so we can set a timer to exit _lingering
    # and make it to the deisred state before the designated time.
    _TM_SVC_MARGIN = 0.020
    # assert _TM_SVC_MARGIN < _TM_SOON

    # Blocking times are used around the time.sleep() operation
    # to obtain more accurate tx/rx execution times on Linux.
    _TM_BLOCKING_MAX = 0.100
    _TM_BLOCKING_MIN = 0.001


    def _dio_isr_clbk(self, dio):
        """A callback given to the PHY for when a DIO pin event occurs.

        The Rpi.GPIO's thread calls this procedure (like an interrupt).
        This procedure posts an Event to this state machine
        corresponding to the DIO pin that transitioned.
        The pin edge's arrival time is the value of the Event.
        """
        now = farc.Framework._event_loop.time()
        self.post_fifo(farc.Event(self._dio_sig_lut[dio], now))


    def _enqueue_action(self, tm, action_args):
        """Enqueues the action at the given time"""
        IOTA = 0.000_000_1  # a small amount of time

        # IMMEDIATELY means this frame jumps to the front of the line
        # put it in the immediate queue (which is serviced before the tm_queue)
        if tm == SX127xHsm.TM_IMMEDIATE:
            self._im_queue.append(action_args)
        else:
            # Ensure this tx time doesn't overwrite an existing one
            # by adding an iota of time if there is a duplicate.
            # This results in FIFO for frames scheduled at the same time.
            tm_orig = tm
            while tm in self._tm_queue:
                tm += IOTA
                # Protect against infinite while-loop
                if tm == tm_orig:
                    IOTA *= 10.0
            self._tm_queue[tm] = action_args


    def _on_lora_rx_done(self):
        """Reads received bytes and meta data from the radio.

        Checks and logs any errors.
        Passes the rx_data to the next layer higher via callback.
        """
        frame_bytes, rssi, snr, flags = self._sx127x.read_lora_rxd()
        if flags == 0:
            # TODO: incr phy_data stats rx done
            self._rx_clbk(self._rxd_hdr_time, frame_bytes, rssi, snr)

        elif flags & SX127x.IRQ_FLAGS_RXTIMEOUT:
            logging.info("PHY._rxing@RXTMOUT")
            # TODO: incr phy_data stats rx tmout

        elif flags & SX127x.IRQ_FLAGS_PAYLDCRCERROR:
            logging.info("PHY._rxing@CRCERR")
            # TODO: incr phy_data stats rx payld crc err


    def _pop_soon_action(self):
        """Returns the next (time, action) pair from the queue and removes it.

        Returns None if the queue is empty.
        """
        if self._im_queue:
            tm = farc.Framework._event_loop.time()
            action = self._im_queue.pop()
            return (tm, action)

        elif self._tm_queue:
            tm = min(self._tm_queue.keys())
            now = farc.Framework._event_loop.time()
            if tm < now + SX127xHsm._TM_SOON:
                action = self._tm_queue[tm]
                del self._tm_queue[tm]
                return (tm, action)
        return None


    def _top_soon_action(self):
        """Returns the next (time, action) pair from the queue without removal.

        Returns None if the queue is empty.
        """
        if self._im_queue:
            tm = SX127xHsm.TM_IMMEDIATE
            action = self._im_queue[-1]
            return (tm, action)

        elif self._tm_queue:
            tm = min(self._tm_queue.keys())
            now = farc.Framework._event_loop.time()
            if tm < now + SX127xHsm._TM_SOON:
                action = self._tm_queue[tm]
                return (tm, action)
        return None
