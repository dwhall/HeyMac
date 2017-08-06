#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE file for details.
"""

import asyncio

from lora_driver import *
from pq import *


class HeyMac(Ahsm):
    """Highly Engineered Yodeling, Medium Access Control
    A class that offers high-level control of the SX127x device
    by using instances of SX127xSpi and SX127xGpio from lora_driver.
    """
    def __init__(self, GpioClass=DraginoLoraGpsHat):

        # Init this Ahsm with the initial pseudo-state
        super().__init__(HeyMac.initial)

        # Instances to control GPIO and SPI peripherals
        self.gpio = GpioClass()
        self.spi = SX127xSpi()

        # Packet receive and transmit queues
        self.rx_queue = Queue()
        self.tx_queue = Queue()

        # Declare DIO events
        self.evt_dio0 = Event(Signal.register("MAC_DIO0"), None)
        self.evt_dio1 = Event(Signal.register("MAC_DIO1"), None)
        self.evt_dio2 = Event(Signal.register("MAC_DIO2"), None)

        # Set GPIO handlers that emit DIO events
        self.gpio.set_dio0_handler(self.dio0_handler)
        self.gpio.set_dio1_handler(self.dio1_handler)
        self.gpio.set_dio2_handler(self.dio2_handler)


    # The GPIO module responds to external I/O in a separate thread.
    # State machine processing should not happen in that thread.
    # So in the following GPIO handlers, we enqueue a unique event for each GPIO.
    # The separate thread will exit quickly back to the main thread
    # and the event will be processed there.
    def dio0_handler(self,): Framework.publish(self.evt_dio0)
    def dio1_handler(self,): Framework.publish(self.evt_dio1)
    def dio2_handler(self,): Framework.publish(self.evt_dio2)


    @staticmethod
    def initial(me, event):
        """Pseudostate: initial
        """
        return me.tran(me, HeyMac.initializing)


    @staticmethod
    def initializing(me, event):
        """State: Initialiaing
        """
        sig = event.signal
        if sig == Signal.ENTRY:
            print("Initializing...")
            if me.spi.check_version():
                print("SPI to LoRa: PASS")
            else:
                pass
            return me.handled(me, event)
        return me.super(me, me.top)


    @staticmethod
    def active(me, event):
        """State: Active
        """
        sig = event.signal
        return me.handled(me, event)


if __name__ == "__main__":
    m = HeyMac()
    m.start(0)

    loop = asyncio.get_event_loop()
    loop.run_forever()
    loop.close()
