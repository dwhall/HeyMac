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
        pq.Framework.subscribe("MAC_DIO1", self)


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
        me.src_addr = b"\xf0\x05\xba\x11\xca\xfe\x26\x00"

        me.te = pq.TimeEvent("MAC_INIT_RETRY")
        me.bcn_te = pq.TimeEvent("MAC_BEACON_TIMER")
        me.lstn_te = pq.TimeEvent("MAC_LISTEN_TMOUT")

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
                me.spi.set_pwr_cfg(boost=True)
                me.spi.set_freq(BCN_FREQ)
                me.spi.set_config(en_crc=True)
                me.spi.set_op_mode('stdby')
                return me.tran(me, me.listening)
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

        elif sig == pq.Signal.MAC_DIO0:
            print("running DIO0 unhandled at lower layer!") # DBG
            return me.handled(me, event)

        elif sig == pq.Signal.MAC_DIO1:
            print("running DIO1 unhandled at lower layer!") # DBG
            return me.handled(me, event)

        return me.super(me, me.top)


    @staticmethod
    def listening(me, event):
        """State: HeyMac:Running:Listening
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("HeyMac Running:Listening")
            me.lstn_te.postIn(me, 8.0) # TODO: magic number

            me.spi.receive()
            return me.handled(me, event)

        elif sig == pq.Signal.MAC_DIO0:
            print("lstn DIO0 RxDone") # TODO: logging
            me.lstn_te.disarm()
            me.lstn_te.postIn(me, 8.0) # TODO: magic number

            # If the rx was good, get the data and stats
            if me.spi.check_rx_flags():
                payld, rssi, snr = me.spi.get_rx()
                print("lstn Rx %d bytes, rssi=%d dBm, snr=%.3f dB" % (len(payld), rssi, snr))
            else:
                print("lstn Rx but pkt was not valid")
            return me.handled(me, event)

        elif sig == pq.Signal.MAC_DIO1:
            print("lstn DIO1 RxTimeout") # TODO: logging
            return me.handled(me, event)

        elif sig == pq.Signal.MAC_LISTEN_TMOUT:
            print("HeyMac Listening timeout")
            return me.tran(me, me.beaconing)

        elif sig == pq.Signal.EXIT:
            me.spi.set_op_mode("stdby")
            return me.handled(me, event)

        return me.super(me, me.running)


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
            # TODO: tx beacon according to bcn slots
            me.asn += 1
            if me.asn % 16 == 0:
                me.bcn.update_asn(me.asn)
                payld = str(me.bcn)
                print(repr(me.bcn), "#len", len(payld), "bytes")
                me.spi.transmit(payld)

            return me.handled(me, event)

        elif sig == pq.Signal.MAC_DIO0:
            # print("bcn DIO0 TxDone") # TODO: logging
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
