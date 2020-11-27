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
    """The physical layer (PHY) state machine that automates
    the behavior of the Semtech SX127x family of radio transceivers.
    """
    # Special time values to use when enqueing a command
    ENQ_TM_NOW = 0  # Use normally for "do it now"
    ENQ_TM_IMMEDIATELY = -1 # Use sparingly to jump the queue

    # The margin within which the Ahsm will transition to
    # the action's state if there is an entry in the action queue;
    # otherwise, transitions to the default state, listening or sleeping.
    _TM_SOON = 0.070

    # The amount of time it takes to get from the _lingering state
    # through _scheduling and to the next action's state.
    # This is used so we can set a timer to exit _lingering
    # and make it to the deisred state before the designated time.
    _TM_SVC_MARGIN = 0.050
#    assert _TM_SVC_MARGIN < _TM_SOON

    # Blocking times are used with the sleep() operation
    # to obtain more accurate tx/rx execution times
    _TM_BLOCKING_MAX = 0.100
    _TM_BLOCKING_MIN = 0.001

    def __init__(self, lstn_by_dflt=True):
        """Listen by default means the radio enters
        continuous-rx mode when it is not doing anything else.
        If this is False, the radio enters sleep mode
        when it is not doing anything else.
        """
        super().__init__()
        self.sx127x = phy_sx127x.PhySX127x()
        self._lstn_by_dflt = lstn_by_dflt
        self._dflt_stngs = ()


#### Public interface

    def enqueue_rx(self, rx_time, rx_stngs, rx_durxn, rx_clbk):
        """Enqueues a receive-once operation
        at the given time for the given duraction
        with the given settings.
        Posts the Reschedule event.
        """
        assert not self._lstn_by_dflt, "enqueue_rx() should not be used when the PHY is listen-by-default.  Use set_dflt_rx() instead."

        # Convert NOW to an actual time
        if rx_time == PhySX127xAhsm.ENQ_TM_NOW:
            rx_time = farc.Framework._event_loop.time()

        # The order of this tuple MUST match (action, stngs, ...)
        rx_data = ("rx", rx_stngs, rx_durxn, rx_clbk)
        self._xfer_queue.append((rx_time, rx_data))
        self.post_fifo(self._evt_reschedule)


    def enqueue_tx(self, tx_time, tx_stngs, tx_bytes):
        """Enqueues the given tx_bytes for transmit
        at the given time with the given settings.
        Posts the Reschedule event.
        """
        assert type(tx_bytes) is bytes

        # Convert NOW to an actual time
        if tx_time == PhySX127xAhsm.ENQ_TM_NOW:
            tx_time = farc.Framework._event_loop.time()

        # The order of this tuple MUST match (action, stngs, ...)
        tx_data = ("tx", tx_stngs, tx_bytes)
        self._xfer_queue.append((tx_time, tx_data))
        self.post_fifo(self._evt_reschedule)


    def set_dflt_stngs(self, dflt_stngs):
        """Stores the default settings for the PHY.
        This must be called before start() so they
        can be written to the device during initilizing.
        """
        self._dflt_stngs = dflt_stngs


    def start_stack(self, ahsm_prio):
        """This is the bottom of the protocol stack,
        so just start this Ahsm
        """
        self.start(ahsm_prio)


#### Private interface

    def _dio_isr_clbk(self, dio):
        """A callback that is given to phy_sx127x
        for when a DIO pin event occurs.
        This procedure posts an Event to this state machine
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
        farc.Signal.register("_PHY_RESCHEDULE")

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
        self._evt_reschedule = farc.Event(farc.Signal._PHY_RESCHEDULE, None)

        # Two time events
        self.tmout_evt = farc.TimeEvent("_PHY_TMOUT")
        self.prdc_evt = farc.TimeEvent("_PHY_PRDC")

        return self.tran(self._initializing)


    @farc.Hsm.state
    def _initializing(self, event):
        """Application initialization
        Instantiates, opens and verifies the SPI driver.
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
            # We actually use three queues:
            # One queue to handle data coming in from an API call
            self._xfer_queue = []
            # And two queues for a hybrid time-sorted queue:
            # One for frames that sort by time
            # It's actually a dict object where the keys are the time value
            self._tm_queue = {}
            # Another for frames that need to be sent immediately
            self._im_queue = []
            return self.handled(event)

        elif sig == farc.Signal._PHY_TMOUT:
            if self.sx127x.open(self._dio_isr_clbk):
                assert len(self._dflt_stngs) > 0, "Default settings must be set before initializing"
                self.sx127x.set_flds(self._dflt_stngs)
                self.sx127x.write_stngs(False)
                return self.tran(self._scheduling)

            logging.info("_initializing: no SX127x or SPI")
            self.tmout_evt.post_in(self, 1.0)
            return self.handled(event)

        elif sig == farc.Signal.EXIT:
            self.tmout_evt.disarm()
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _scheduling(self, event):
        """Writes any outstanding settings and always
        transitions to _txing, _sleeping or _listening
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._scheduling")
            assert self.sx127x.OPMODE_STBY == self.sx127x.read_opmode()

            # Move items from the transfer queue to the action queue
            # FIXME: this is not thread safe (but is good enough for now)
            q = self._xfer_queue.copy()
            self._xfer_queue.clear()
            for tm, action in q:
                self._enqueue_action(tm, action)

            self.post_fifo(farc.Event(farc.Signal._ALWAYS, None))
            return self.handled(event)

        elif sig == farc.Signal._ALWAYS:
            # Get the next explicit action or use the default
            next_action = self._top_action()
            if next_action:
                tm, action = next_action
            else:
                tm = action = None

            # If the action happens soon, go to its state
            now = farc.Framework._event_loop.time()
            if action and tm < now + PhySX127xAhsm._TM_SOON:
                if action[0] == "rx":
                    st = self._listening
                elif action[0] == "tx":
                    st = self._txing
                else:
                    # Placeholder for CAD
                    assert True, "Got here by accident"

            # Otherwise, go to the default action's state
            elif self._lstn_by_dflt:
                st = self._listening
            else:
                st = self._sleeping

            return self.tran(st)

        return self.super(self.top)


    @farc.Hsm.state
    def _lingering(self, event):
        """This state was created strictly to handle
        the timer behavior that is duplicated by the
        _listening and _sleeping states.
        On entry, starts a timer for when to exit
        to go handle the next action in the queue.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._lingering")
            # Start a timer for the next action
            next_action = self._top_action()
            if next_action:
                tm, action = next_action
                self.tmout_evt.post_at(self, tm - PhySX127xAhsm._TM_SVC_MARGIN)
            return self.handled(event)

        elif sig == farc.Signal._PHY_RESCHEDULE:
            return self.tran(self._scheduling)

        elif sig == farc.Signal.EXIT:
            self.tmout_evt.disarm()
            # Change modes ("near instantaneous" for rx & sleep)
            self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_STBY, False)
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _listening(self, event):
        """Puts the device into receive mode
        either because of a receive action or listen-by-default.
        Transitions to _rxing if a valid header is received.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._lingering._listening")

            # Get the next action from the queue
            next_action = self._pop_action()
            if next_action:
                rx_time, rx_data = next_action
                (action, rx_stngs, rx_durxn, rx_clbk) = rx_data
                assert action == "rx"
                self._rx_clbk = rx_clbk
            else:
                #rx_stngs = self._dflt_rx_stngs
                rx_stngs = ()
                #self._rx_clbk = self._dflt_rx_clbk

            # Write RX settings from higher layer and needed by this PHY
            stngs = list(rx_stngs)
            stngs.extend((("FLD_RDO_DIO0", 0),  # _DIO_RX_DONE
                          ("FLD_RDO_DIO1", 0),  # _DIO_RX_TMOUT
                          ("FLD_RDO_DIO3", 1))) # _DIO_VALID_HDR
            self.sx127x.set_flds(stngs)
            self.sx127x.write_stngs(True)

            # Prep interrupts for RX
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

            # Start periodic event for update_rng()
            self.prdc_evt.post_every(self, 0.100)  # 100ms

            # Start receiver
            if self._lstn_by_dflt:
                self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_RXCONT, False)
            else:
                # Blocking sleep until rx_time (assuming a short amount)
                now = farc.Framework._event_loop.time()
                tiny_sleep = rx_time - now
                assert tiny_sleep > 0.0, "didn't beat action time, need to increase _TM_SVC_MARGIN"
                if tiny_sleep > PhySX127xAhsm._TM_BLOCKING_MAX:
                    tiny_sleep = PhySX127xAhsm._TM_BLOCKING_MAX
                if tiny_sleep > PhySX127xAhsm._TM_BLOCKING_MIN:
                    time.sleep(tiny_sleep)

                self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_RXONCE, False)
                self.tmout_evt.post_in(self, rx_durxn)
            return self.handled(event)

        elif sig == farc.Signal._PHY_PRDC:
            self.sx127x.updt_rng()
            return self.handled(event)

        elif sig == farc.Signal._PHY_TMOUT:
            return self.tran(self._scheduling)

        elif sig == farc.Signal._DIO_PAYLD_CRC_ERR:
            # This DIO signal might never occur in this state
            # (only get payld after a valid hdr, be in _rxing state)
            assert True, "Got here; keep this"
            # TODO: log dio rx payld crc err
            # TODO: incr lnk_data stats crc err cnt
            return self.tran(self._scheduling)

        elif sig == farc.Signal._DIO_RX_TMOUT:
            # TODO: log pkt stats
            return self.tran(self._scheduling)

        elif sig == farc.Signal._DIO_VALID_HDR:
            self._rxd_hdr_time = event.value
            return self.tran(self._rxing)

        elif sig == farc.Signal.EXIT:
            self.prdc_evt.disarm()
            return self.handled(event)

        return self.super(self._lingering)


    @farc.Hsm.state
    def _sleeping(self, event):
        """Puts the device into sleep mode.
        Timer and timeout handling is performed
        by the parent state, _lingering()
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._lingering._sleeping")
            self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_SLEEP, False)
            return self.handled(event)

        return self.super(self._lingering)


    @farc.Hsm.state
    def _rxing(self, event):
        """Continues a reception in progress.
        Protects reception by NOT reacting to the _PHY_RESCHEDULE event.
        Transitions to _scheduling after reception ends for whatever reason.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._rxing")
            self.tmout_evt.post_in(self, 1.0) # TODO: calc soft timeout delta
            return self.handled(event)

        elif sig == farc.Signal._DIO_PAYLD_CRC_ERR:
            # TODO: log dio rx payld crc err
            # TODO: incr phy_data stats crc err cnt
            return self.tran(self._scheduling)

        elif sig == farc.Signal._DIO_RX_TMOUT:
            # TODO: log dio rx tmout
            # TODO: incr phy_data stats rx tmout
            return self.tran(self._scheduling)

        elif sig == farc.Signal._DIO_RX_DONE:
            self._handle_lora_rx_done()
            return self.tran(self._scheduling)

        elif sig == farc.Signal._PHY_TMOUT:
            logging.warning("PHY._rxing@_PHY_TMOUT")
            self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_STBY, False)
            return self.tran(self._scheduling)

        elif sig == farc.Signal.EXIT:
            self.tmout_evt.disarm()
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _txing(self, event):
        """Prepares for transmission, transmits,
        awaits DIO_TX_DONE event from radio,
        then transitions to the _scheduling state.
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            logging.debug("PHY._txing")
            tx_action = self._pop_action()
            (tx_time, tx_data) = tx_action
            (action, tx_stngs, tx_bytes) = tx_data
            assert action == "tx"

            # Write TX settings from higher layer and needed by this PHY
            stngs = list(tx_stngs)
            stngs.append(("FLD_RDO_DIO0", 1))   # _DIO_TX_DONE
            self.sx127x.set_flds(stngs)
            self.sx127x.write_stngs(False)

            # Prep interrupts for TX
            self.sx127x.write_lora_irq_mask(
                phy_sx127x.PhySX127x.IRQ_FLAGS_ALL,     # disable these
                phy_sx127x.PhySX127x.IRQ_FLAGS_TXDONE  #enable these
            )

            # Write payload into radio's FIFO
            self.sx127x.write_fifo_ptr(0x00)
            self.sx127x.write_fifo(tx_bytes)

            # Blocking sleep until tx_time (assuming a short amount)
            now = farc.Framework._event_loop.time()
            tiny_sleep = tx_time - now
            #assert tiny_sleep > 0.0, "didn't beat action time, need to increase _TM_SVC_MARGIN"
            if tiny_sleep > PhySX127xAhsm._TM_BLOCKING_MAX:
                tiny_sleep = PhySX127xAhsm._TM_BLOCKING_MAX
            if tiny_sleep > 0.001:
                time.sleep(tiny_sleep)

            # Start software timer for backup
            self.tmout_evt.post_in(self, 1.0) # TODO: calc soft timeout delta

            # Start transmission and await DIO_TX_DONE
            self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_TX, False)
            return self.handled(event)

        elif sig == farc.Signal._DIO_TX_DONE:
            return self.tran(self._scheduling)

        elif sig == farc.Signal._PHY_TMOUT:
            logging.warning("PHY._txing@_PHY_TMOUT")
            self.sx127x.write_opmode(phy_sx127x.PhySX127x.OPMODE_STBY, True)
            return self.handled(event)

        elif sig == farc.Signal._DIO_MODE_RDY:
            return self.tran(self._scheduling)

        elif sig == farc.Signal.EXIT:
            self.tmout_evt.disarm()
            return self.handled(event)

        return self.super(self.top)


#### Private methods

    def _enqueue_action(self, tm, action_data):
        """Enqueues the action at the given time
        """
        IOTA = 0.000_000_1  # a small amount of time

        # IMMEDIATELY means this frame jumps to the front of the line
        # put it in the immediate queue (which is serviced before the tm_queue)
        if tm == PhySX127xAhsm.ENQ_TM_IMMEDIATELY:
            self._im_queue.append(action_data)
        else:
            # Ensure this tx time doesn't overwrite an existing one
            # by adding an iota of time if there is a duplicate.
            # This results in FIFO for frames scheduled at the same time.
            while tm in self._tm_queue:
                tm += IOTA
            self._tm_queue[tm] = action_data


    def _handle_lora_rx_done(self,):
        """Reads received bytes and meta data from the radio.
        Checks and logs any errors.
        Passes the rx_data to the next layer higher via callback.
        """
        frame_bytes, rssi, snr = self.sx127x.read_lora_rxd()
        # TODO: check sx127x for any rx errors
        if True: # no errors
            # TODO: log rx done
            # TODO: incr lnk_data stats rx done
            #self._rx_clbk(frame_bytes, self._rxd_hdr_time, rssi, snr)
            pass

        else: # errors
            # TODO: log err_type
            # TODO: incr lnk_data stats rx err
            pass


    def _pop_action(self,):
        """Returns the next action from the queue and removes it.
        If there is an immediate fifo action, returns it;
        otherwise returns the action with the smallest time.
        Returns None if the queue is empty.
        """
        if self._im_queue:
            tm = farc.Framework._event_loop.time()
            action = self._im_queue.pop()
        elif self._tm_queue:
            tm = min(self._tm_queue.keys())
            action = self._tm_queue[tm]
            del self._tm_queue[tm]
        else:
            return None
        return (tm, action)


    def _top_action(self,):
        """Returns the next action from the queue without removing it.
        If there is an immediate fifo action, returns it;
        otherwise returns the action with the smallest time.
        Returns None if the queue is empty.
        """
        if self._im_queue:
            tm = farc.Framework._event_loop.time()
            action = self._im_queue[-1]
        elif self._tm_queue:
            tm = min(self._tm_queue.keys())
            action = self._tm_queue[tm]
        else:
            return None
        return (tm, action)
