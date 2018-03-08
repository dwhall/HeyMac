#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.

Physical Layer State Machine for SPI operations to the SX127x device
- models SX127x device operation
- establishes Transmit and Receive sequences
- responds to a handful of events (expected from Layer 2 (MAC))
"""

import time

import lora_driver, pq

import phy_cfg


class SX127xSpiAhsm(pq.Ahsm):

    @staticmethod
    def initial(me, event):
        """Pseudostate: SX127xSpiAhsm:initial
        """
        # self-signaling
        pq.Signal.register("ALWAYS")

        # Outgoing
        pq.Signal.register("PHY_RX_DATA")

        # Incoming from higher layer
        pq.Framework.subscribe("CFG_LORA", me)
        pq.Framework.subscribe("SLEEP", me)
        pq.Framework.subscribe("CAD", me)
        pq.Framework.subscribe("RECEIVE", me)
        pq.Framework.subscribe("TRANSMIT", me)

        # Incoming from GPIO (SX127x's DIO pins)
        pq.Framework.subscribe("PHY_DIO0", me)
        pq.Framework.subscribe("PHY_DIO1", me)
        pq.Framework.subscribe("PHY_DIO3", me)
        pq.Framework.subscribe("PHY_DIO4", me)

        me.sx127x = lora_driver.SX127xSpi()

        return me.tran(me, SX127xSpiAhsm.initializing)


    @staticmethod
    def initializing(me, event):
        """State: SX127xSpiAhsm:initializing
        Reads SX127x regs and transitions to 
        the idling or sleeping state.
        If SPI cannot talk to a SX127x,
        remains in initializing state
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            if me.sx127x.check_chip_ver():
                me.sx127x.get_regs()
                me.sx127x.set_op_mode('stdby') # FIXME: TEMPORARY!  
                me.postFIFO(pq.Event(pq.Signal.ALWAYS, None))
            else:
                # TODO: no SX127x or no SPI
                pass
            return me.handled(me, event)

        elif sig == pq.Signal.ALWAYS:
            # TODO: if lora and stdby: trans(idling) else: trans(sleeping)
            return me.tran(me, SX127xSpiAhsm.idling)

        return me.super(me, me.top)


    @staticmethod
    def idling(me, event):
        """State: SX127xSpiAhsm:idling
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            return me.handled(me, event)

        elif sig == pq.Signal.CFG_LORA:
            me.sx127x.set_config(event.value)
            me.sx127x.set_pwr_cfg(boost=True)
            return me.handled(me, event)
        
        elif sig == pq.Signal.SLEEP:
            return me.tran(me, me.sleeping)

        elif sig == pq.Signal.RECEIVE:
            me.rx_time = event.value[0]
            me.rx_freq = event.value[1]
            return me.tran(me, me.rx_prepping)

        elif sig == pq.Signal.TRANSMIT:
            me.tx_time = event.value[0]
            me.tx_freq = event.value[1]
            me.tx_data = event.value[2]
            return me.tran(me, me.tx_prepping)

        elif sig == pq.Signal.CAD:
            return me.tran(me, me.cad_ing)

        return me.super(me, me.top)

#### Receive chain
    @staticmethod
    def rx_prepping(me, event):
        """State: SX127xSpiAhsm:idling:rx_prepping
        While still in radio's standby mode,
        get regs and FIFO ready for RX.
        Always transfer to Frequency Synth RX mode.
        """
        MAX_BLOCK_TIME = 0.050 # secs

        sig = event.signal
        if sig == pq.Signal.ENTRY:

            # Enable only the RX interrupts (disable all others)
            me.sx127x.disable_irqs()
            me.sx127x.enable_irqs(lora_driver.IRQFLAGS_RXTIMEOUT_MASK
                | lora_driver.IRQFLAGS_RXDONE_MASK
                | lora_driver.IRQFLAGS_PAYLOADCRCERROR_MASK)

            # Prepare DIO0,1 to cause RxDone, RxTimeout interrupts
            me.sx127x.set_dio_mapping(dio0=0, dio1=0)
            me.sx127x.set_rx_fifo()
            me.sx127x.set_rx_freq(me.rx_freq)

            # Reminder pattern 
            me.postFIFO(pq.Event(pq.Signal.ALWAYS, None))
            return me.handled(me, event)

        elif sig == pq.Signal.ALWAYS:
            tiny_sleep = me.rx_time - pq.Framework._event_loop.time()
            if 0.0 < tiny_sleep < MAX_BLOCK_TIME:
                time.sleep(tiny_sleep)
            return me.tran(me, SX127xSpiAhsm.receiving)

        return me.super(me, me.idling)


    @staticmethod
    def receiving(me, event):
        """State SX127xSpiAhsm:receiving
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
#            print("rx_time        ", me.rx_time)
#            print("rxonce         ", pq.Framework._event_loop.time())
            me.sx127x.set_op_mode(mode="rxonce")
            return me.handled(me, event)
        
        elif sig == pq.Signal.PHY_DIO0: # RX_DONE
            rxd_time = event.value
            if me.sx127x.check_rx_flags():
                payld, rssi, snr = me.sx127x.get_rx()
                pkt_data = (rxd_time, payld, rssi, snr)
                pq.Framework.publish(pq.Event(pq.Signal.PHY_RX_DATA, pkt_data))
            else:
                # TODO: crc error stats
                print("rx CRC error")

            return me.tran(me, SX127xSpiAhsm.idling)

        elif sig == pq.Signal.PHY_DIO1: # RX_TIMEOUT
            me.sx127x.clear_irqs(lora_driver.IRQFLAGS_RXTIMEOUT_MASK)
            return me.tran(me, SX127xSpiAhsm.idling)

        elif sig == pq.Signal.PHY_DIO3: # ValidHeader
            # TODO: future: DIO3  for earlier rx_time capture
            return me.handled(me, event)

        return me.super(me, me.top)


#### Transmit chain
    @staticmethod
    def tx_prepping(me, event):
        """State: SX127xSpiAhsm:idling:tx_prepping
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:

            # Enable only the TX interrupts (disable all others)
            me.sx127x.disable_irqs()
            me.sx127x.enable_irqs(lora_driver.IRQFLAGS_TXDONE_MASK)
            me.sx127x.clear_irqs(lora_driver.IRQFLAGS_TXDONE_MASK)

            # Prepare DIO0 to cause TxDone interrupt
            me.sx127x.set_dio_mapping(dio0=1)
            me.sx127x.set_tx_data(me.tx_data)

            me.sx127x.set_tx_freq(me.tx_freq)

            # Reminder pattern 
            me.postFIFO(pq.Event(pq.Signal.ALWAYS, None))
            return me.handled(me, event)

        elif sig == pq.Signal.ALWAYS:
            # Calculate precise sleep time and apply a TX margin
            # to allow receivers time to get ready
            tiny_sleep = me.tx_time - pq.Framework._event_loop.time()
            tiny_sleep += phy_cfg.tx_margin

            # If TX time has passed, don't sleep
            # Else use sleep to get ~1ms precision
            # Cap sleep at 50ms so we don't block for too long
            if 0.0 < tiny_sleep: # because MAC layer uses 40ms PREP time
                if tiny_sleep > 0.050:
                    tiny_sleep = 0.050
                time.sleep(tiny_sleep)
            return me.tran(me, SX127xSpiAhsm.transmitting)

        return me.super(me, me.idling)


    @staticmethod
    def transmitting(me, event):
        """State: SX127xSpiAhsm:transmitting
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("tx_time        ", me.tx_time)
            print("tx             ", pq.Framework._event_loop.time())
            me.sx127x.set_op_mode(mode="tx")
            return me.handled(me, event)

        elif sig == pq.Signal.PHY_DIO0: # TX_DONE
            return me.tran(me, SX127xSpiAhsm.idling)

        return me.super(me, me.top)

