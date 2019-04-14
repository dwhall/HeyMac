#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.

Physical Layer State Machine for GPIO operations on the RasPi device
- detects DIO* pin changes from the SX127x device
- detects PPS pin changes from the GPS device
- publishes events (with timestamp) when these pin changes occur
"""


import farc

try:
    import RPi.GPIO as GPIO
except:
    from . import mock_gpio as GPIO


# The RPi.GPIO module responds to external I/O in a separate thread.
# State machine processing should not happen in that thread.
# So in the following GPIO handler, we publish a unique event for each GPIO.
# The separate thread will publish the event and exit quickly
# back to the main thread; the event will be processed there.
def gpio_input_handler(sig):
    """Emits the given signal upon a pin change.
    The event's value is the current time.
    """
    time = farc.Framework._event_loop.time()
    evt = farc.Event(sig, time)
    farc.Framework.publish(evt)


class GpioAhsm(farc.Ahsm):

    @farc.Hsm.state
    def initial(me, event):
        """Pseudostate: GpioAhsm:initial
        """
        GPIO.setmode(GPIO.BCM)

        farc.Signal.register("_ALWAYS")
        return me.tran(me, GpioAhsm.running)


    @farc.Hsm.state
    def running(me, event):
        """State: GpioAhsm:running
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return me.handled(me, event)

        elif sig == farc.Signal.SIGTERM:
            return me.tran(me, me.exiting)

        elif sig == farc.Signal.EXIT:
            GPIO.cleanup()
            return me.handled(me, event)

        return me.super(me, me.top)


    @farc.Hsm.state
    def exiting(me, event):
        """State: GpioAhsm:exiting
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return me.handled(me, event)

        return me.super(me, me.top)


    def register_pin_in(self, pin_nmbr, pin_edge, sig_name):
        """Registers a signal to be published when the input pin edge is detected.
        """
        sig_num = farc.Signal.register(sig_name)
        GPIO.setup(pin_nmbr, GPIO.IN)
        GPIO.add_event_detect(pin_nmbr, edge=pin_edge, callback=lambda x: gpio_input_handler(sig_num))


    def register_pin_out(self, pin_nmbr, pin_initial):
        """Registers an output pin to be set with an initial value.
        """
        GPIO.setup(pin_nmbr, GPIO.OUT, initial=pin_initial)
