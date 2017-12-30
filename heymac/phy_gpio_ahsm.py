#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.

Physical Layer State Machine for GPIO operations on the RasPi device
- detects DIO* pin changes from the SX127x device
- detects PPS pin changes from the GPS device
- publishes events when these pin changes occur (includes time of change)
"""


import time

import RPi.GPIO as GPIO

import pq


# TODO: move to config file
reset = {"pin":17, "sig_name":"GPS_RST"}
dio0 = {"pin":4, "sig_name":"DIO0"}
dio1 = {"pin":23, "sig_name":"DIO1"}
dio2 = {"pin":24, "sig_name":"DIO2"}
pps = {"pin":26, "sig_name":"PPS"}


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
    print("GPIO publish", evt)
    pq.Framework.publish(evt)


class GpioAhsm(pq.Ahsm):

    @staticmethod
    def initial(me, event):
        """Pseudostate: GpioAhsm:initial
        """
        pq.Signal.register("ALWAYS")

        # Register signals to emit upon pin change
        me.sig_dio0 = pq.Signal.register(dio0["sig_name"])
        me.sig_dio1 = pq.Signal.register(dio1["sig_name"])
        me.sig_dio2 = pq.Signal.register(dio2["sig_name"])
        me.sig_pps = pq.Signal.register(pps["sig_name"])

        return me.tran(me, GpioAhsm.initializing)

    @staticmethod
    def initializing(me, event):
        """State: GpioAhsm:initializing
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            GPIO.setmode(GPIO.BCM)

            # Set pins directions
            GPIO.setup(dio0["pin"], GPIO.IN)
            GPIO.setup(dio1["pin"], GPIO.IN)
            GPIO.setup(dio2["pin"], GPIO.IN)
            GPIO.setup(pps["pin"], GPIO.IN)
            GPIO.setup(reset["pin"], GPIO.OUT, initial=GPIO.HIGH)

            # Set callback to happen on pin change
            GPIO.add_event_detect(dio0["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_dio0))
            GPIO.add_event_detect(dio1["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_dio1))
            GPIO.add_event_detect(dio2["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_dio2))
            GPIO.add_event_detect(pps["pin"], edge=GPIO.RISING, callback=lambda x: gpio_input_handler(me.sig_pps))

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
