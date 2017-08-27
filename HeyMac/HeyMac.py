#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE file for details.
"""

import asyncio

import lora_driver, pq
import HeyMacBeacon


# Radio Frequency for beacon transmissions
BCN_FREQ = 434.000e6


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

        # Subscribe to DIO events
        pq.Framework.subscribe("MAC_DIO0", self)

    # The GPIO module responds to external I/O in a separate thread.
    # State machine processing should not happen in that thread.
    # So in the following GPIO handlers, we enqueue a unique event for each GPIO.
    # The separate thread will exit quickly back to the main thread
    # and the event will be processed there.
    def dio0_handler(self, chnl): pq.Framework.publish(self.evt_dio0)
    def dio1_handler(self, chnl): pq.Framework.publish(self.evt_dio1)
    def dio2_handler(self, chnl): pq.Framework.publish(self.evt_dio2)


    @staticmethod
    def initial(me, event):
        """Pseudostate: HeyMac:initial
        """
        me.asn = 0
        me.src_addr = "\xf0\x05\xba\x11\xca\xfe\x26\x00"

        me.te = pq.TimeEvent("MAC_INIT_RETRY")
        me.bcn_te = pq.TimeEvent("MAC_BEACON_TIMER")
        return me.tran(me, HeyMac.initializing)


    @staticmethod
    def initializing(me, event):
        """State: HeyMac:Initializing
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("HeyMac Initializing") # TODO: logging
            me.te.postIn(me, 0.0)
            return me.handled(me, event)

        elif sig == pq.Signal.MAC_INIT_RETRY:
            if me.spi.check_chip_ver():
                me.spi.set_freq(BCN_FREQ)
                me.spi.set_config(en_crc=True)
                return me.tran(me, me.beaconing)
            else:
                me.te.postIn(me, 0.500)
                return me.handled(me, event)

            # TODO read chip's current config

        return me.super(me, me.top)


    @staticmethod
    def running(me, event):
        """State: HeyMac:Running
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("HeyMac Running") # TODO: logging
            return me.handled(me, event)

        return me.super(me, me.top)


    @staticmethod
    def beaconing(me, event):
        """State: HeyMac:Running:Beaconing
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("HeyMac Running:Beaconing") # TODO: logging
            me.bcn = HeyMacBeacon.HeyMacBeacon(me.src_addr, me.asn, 0, None, None)
            me.bcn_te.postEvery(me, 0.250)
            return me.handled(me, event)

        elif sig == pq.Signal.MAC_BEACON_TIMER:
            me.asn += 1

            # TODO: tx beacon according to bcn slots
            if me.asn % 16 == 0:
                me.bcn.update_asn(me.asn)
                print("bcn:", me.asn)
                me.spi.transmit(str(me.bcn))

            return me.handled(me, event)

        elif sig == pq.Signal.MAC_DIO0:
            print("bcn DIO0 TxDone") # TODO: logging
            return me.handled(me, event)

        elif sig == pq.Signal.EXIT:
            me.bcn_te.disarm()
            return me.handled(me, event)

        return me.super(me, me.running)


    @staticmethod
    def sleeping(me, event):
        """State: HeyMac:Sleeping
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("HeyMac Sleeping") # TODO: logging
            return me.handled(me, event)

        return me.super(me, me.top)


if __name__ == "__main__":
    m = HeyMac()
    m.start(0)

    loop = asyncio.get_event_loop()
    loop.run_forever()
    loop.close()
