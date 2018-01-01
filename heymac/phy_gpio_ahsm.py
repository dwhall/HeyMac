#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.

Physical Layer State Machine for GPIO operations on the RasPi device
- detects DIO* pin changes from the SX127x device
- detects PPS pin changes from the GPS device
- publishes events when these pin changes occur (includes time of change)
"""


import RPi.GPIO as GPIO

import pq

import phy_cfg


# The GPIO module responds to external I/O in a separate thread.
# State machine processing should not happen in that thread.
# So in the following GPIO handler, we publish a unique event for each GPIO.
# The separate thread will exit quickly back to the main thread
# and the event will be processed there.
def gpio_input_handler(sig):
    """Emits the given signal upon a pin change.
    The value is the time of the pin change.
    """
    time = pq.Framework._event_loop.time()
    evt = pq.Event(sig, time)
    pq.Framework.publish(evt)


class GpioAhsm(pq.Ahsm):

    @staticmethod
    def initial(me, event):
        """Pseudostate: GpioAhsm:initial
        """
        pq.Signal.register("ALWAYS")

        # Register signals to emit upon pin change
        me.sig_dio0 = pq.Signal.register(phy_cfg.dio0["sig_name"])
        me.sig_dio1 = pq.Signal.register(phy_cfg.dio1["sig_name"])
        me.sig_dio2 = pq.Signal.register(phy_cfg.dio2["sig_name"])
        me.sig_pps = pq.Signal.register(phy_cfg.pps["sig_name"])

        return me.tran(me, GpioAhsm.initializing)

    @staticmethod
    def initializing(me, event):
        """State: GpioAhsm:initializing
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            GPIO.setmode(GPIO.BCM)

            # Set pins directions
            GPIO.setup(phy_cfg.dio0["pin"], GPIO.IN)
            GPIO.setup(phy_cfg.dio1["pin"], GPIO.IN)
            GPIO.setup(phy_cfg.dio2["pin"], GPIO.IN)
            GPIO.setup(phy_cfg.pps["pin"], GPIO.IN)
            GPIO.setup(phy_cfg.reset["pin"], GPIO.OUT, initial=GPIO.HIGH)

            # Set callback to happen on pin change
            GPIO.add_event_detect(phy_cfg.dio0["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_dio0))
            GPIO.add_event_detect(phy_cfg.dio1["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_dio1))
            GPIO.add_event_detect(phy_cfg.dio2["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_dio2))
            GPIO.add_event_detect(phy_cfg.pps["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_pps))

            me.postFIFO(pq.Event(pq.Signal.ALWAYS, None))
            return me.handled(me, event)

        elif sig == pq.Signal.ALWAYS:
            return me.tran(me, GpioAhsm.running)

        return me.super(me, me.top)


    @staticmethod
    def running(me, event):
        """State: GpioAhsm:running
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            return me.handled(me, event)
        
        elif sig == pq.Signal.SIGTERM:
            return me.tran(me, me.exiting)

        elif sig == pq.Signal.EXIT:
            GPIO.cleanup()
            return me.handled(me, event)
        
        return me.super(me, me.top)


    @staticmethod
    def exiting(me, event):
        """State: GpioAhsm:exiting
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            return me.handled(me, event)

        return me.super(me, me.top)
