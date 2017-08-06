#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE file for details.
"""

import asyncio

import lora_driver, pq


class HeyMac(pq.Ahsm):
    """Highly Engineered Yodeling, Medium Access Control
    A class that offers high-level control of the SX127x device
    by using instances of SX127xSpi and SX127xGpio from lora_driver.
    """
    def __init__(self, GpioClass=lora_driver.DraginoLoraGpsHat):

        # Init this Ahsm with the initial pseudo-state
        super().__init__(HeyMac.initial)

        # Instances to control GPIO and SPI peripherals
        self.gpio = GpioClass()
        self.spi = lora_driver.SX127xSpi()

        # Packet receive and transmit queues
        self.rx_queue = lora_driver.Queue()
        self.tx_queue = lora_driver.Queue()

        # Declare DIO events
        self.evt_dio0 = pq.Event(pq.Signal.register("MAC_DIO0"), None)
        self.evt_dio1 = pq.Event(pq.Signal.register("MAC_DIO1"), None)
        self.evt_dio2 = pq.Event(pq.Signal.register("MAC_DIO2"), None)

        # Set GPIO handlers that emit DIO events
        self.gpio.set_dio0_handler(self.dio0_handler)
        self.gpio.set_dio1_handler(self.dio1_handler)
        self.gpio.set_dio2_handler(self.dio2_handler)


    # The GPIO module responds to external I/O in a separate thread.
    # State machine processing should not happen in that thread.
    # So in the following GPIO handlers, we enqueue a unique event for each GPIO.
    # The separate thread will exit quickly back to the main thread
    # and the event will be processed there.
    def dio0_handler(self,): pq.Framework.publish(self.evt_dio0)
    def dio1_handler(self,): pq.Framework.publish(self.evt_dio1)
    def dio2_handler(self,): pq.Framework.publish(self.evt_dio2)


    @staticmethod
    def initial(me, event):
        """Pseudostate: initial
        """
        me.te = pq.TimeEvent("MAC_INIT_RETRY")
        return me.tran(me, HeyMac.initializing)


    @staticmethod
    def initializing(me, event):
        """State: Initialiaing
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("HeyMac Initializing...") # TODO: logging
            me.te.postIn(me, 0)
#            me.postFIFO(pq.Event(pq.Signal.MAC_INIT_RETRY, None)) # FIXME: This doesn't get processed until Ctrl+C
            return me.handled(me, event)

        elif sig == pq.Signal.MAC_INIT_RETRY:
            if me.spi.check_version():
                print("SPI to LoRa: PASS")
                return me.tran(me, HeyMac.active)
            else:
                print("SPI to LoRa: FAIL")
                me.te.postIn(me, 0.5)
                return me.handled(me, event)

        return me.super(me, me.top)


    @staticmethod
    def active(me, event):
        """State: Active
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("HeyMac active") # TODO: logging
            return me.handled(me, event)

        return me.super(me, me.top)


if __name__ == "__main__":
    m = HeyMac()
    m.start(0)

    loop = asyncio.get_event_loop()
    loop.run_forever()
    loop.close()
