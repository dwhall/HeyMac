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

from . import phy_cfg


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
        farc.Signal.register("_ALWAYS")

        # Register signals to emit upon pin change
        me.sig_dio0 = farc.Signal.register(phy_cfg.dio0["sig_name"])
        me.sig_dio1 = farc.Signal.register(phy_cfg.dio1["sig_name"])
        me.sig_dio2 = farc.Signal.register(phy_cfg.dio2["sig_name"])
        me.sig_dio3 = farc.Signal.register(phy_cfg.dio3["sig_name"])
        me.sig_dio4 = farc.Signal.register(phy_cfg.dio4["sig_name"])
        me.sig_dio5 = farc.Signal.register(phy_cfg.dio5["sig_name"])
        me.sig_pps = farc.Signal.register(phy_cfg.pps["sig_name"])

        return me.tran(me, GpioAhsm.initializing)

    @farc.Hsm.state
    def initializing(me, event):
        """State: GpioAhsm:initializing
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            GPIO.setmode(GPIO.BCM)

            # Set pins directions
            GPIO.setup(phy_cfg.dio0["pin"], GPIO.IN)
            GPIO.setup(phy_cfg.dio1["pin"], GPIO.IN)
            GPIO.setup(phy_cfg.dio2["pin"], GPIO.IN)
            GPIO.setup(phy_cfg.dio3["pin"], GPIO.IN)
            GPIO.setup(phy_cfg.dio4["pin"], GPIO.IN)
            GPIO.setup(phy_cfg.dio5["pin"], GPIO.IN)
            GPIO.setup(phy_cfg.pps["pin"], GPIO.IN)
            GPIO.setup(phy_cfg.reset["pin"], GPIO.OUT, initial=GPIO.HIGH)

            # Set callback to happen on pin change
            GPIO.add_event_detect(phy_cfg.dio0["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_dio0))
            GPIO.add_event_detect(phy_cfg.dio1["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_dio1))
            GPIO.add_event_detect(phy_cfg.dio2["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_dio2))
            GPIO.add_event_detect(phy_cfg.dio3["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_dio3))
            GPIO.add_event_detect(phy_cfg.dio4["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_dio4))
            GPIO.add_event_detect(phy_cfg.dio5["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_dio5))
            GPIO.add_event_detect(phy_cfg.pps["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_pps))

            # Reminder pattern
            me.postFIFO(farc.Event(farc.Signal._ALWAYS, None))
            return me.handled(me, event)

        elif sig == farc.Signal._ALWAYS:
            return me.tran(me, GpioAhsm.running)

        return me.super(me, me.top)


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
