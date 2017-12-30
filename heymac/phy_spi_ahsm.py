#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.
"""


import pq
from lora_driver import SX127xSpi


class SX127xSpiAhsm(pq.Ahsm):

    @staticmethod
    def initial(me, event):
        """Pseudostate: SX127xSpiAhsm:initial
        """
        # Incoming from higher layer
        pq.Signal.register("CFG_LORA")
        pq.Signal.register("SLEEP")
        pq.Signal.register("CAD")
        pq.Signal.register("RECEIVE")
        pq.Signal.register("TRANSMIT")

        # Incoming from GPIO (SX127x's DIO pins)
        pq.Signal.register("DIO0")
        pq.Signal.register("DIO1")
        pq.Signal.register("DIO3")
        pq.Signal.register("DIO4")

        # self-signaling
        pq.Signal.register("ALWAYS")

        # Outgoing
        pq.Signal.register("RX_DATA")

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
            if SX127xSpi.check_chip_ver():
                SX127xSpi.get_regs()
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
       # if sig == pq.Signal.ENTRY:
       #      return me.handled(me, event)

        if sig == pq.Signal.CFG_LORA:
            SX127xSpi.set_config(event.value)
            return me.handled(me, event)
        
        elif sig == pq.Signal.SLEEP:
            return me.tran(me, me.sleeping)

        elif sig == pq.Signal.RECEIVE:
            me.rx_time = event.value
            return me.tran(me, me.rx_prepping)

        elif sig == pq.Signal.TRANSMIT:
            me.tx_time = event.value
            return me.tran(me, me.tx_prepping)

        elif sig == pq.Signal.CAD:
            return me.tran(me, me.cad_ing)

        return me.super(me, me.top)

#### Receive chain
    @staticmethod
    def rx_prepping(me, event):
        """State: HeyMac:idling:rx_prepping
        While still in radio's standby mode,
        get regs and FIFO ready for RX.
        Always transfer to Frequency Synth RX mode.
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            rx_time = event.value

            # Prepare DIO0,1 to cause RxDone, RxTimeout interrupts
            SX127xSpi.enable_irqs(SX127xSpi.IRQFLAGS_RXTIMEOUT_MASK 
                | SX127xSpi.IRQFLAGS_RXDONE_MASK)
            SX127xSpi.set_dio_mapping(dio0=0, dio1=0)
            SX127xSpi.set_rx_fifo()

            #TODO set timer to RX at appropriate time

            # Reminder pattern to trans to fsrxing
            me.postFIFO(pq.Event(pq.Signal.ALWAYS, None))
            return me.handled(me, event)

        elif sig == pq.Signal.ALWAYS:
            return me.tran(me, SX127xSpiAhsm.fsrxing)

        return me.super(me, me.idling)


    @staticmethod
    def fsrxing(me, event):
        """State: HeyMac:fsrxing
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            SX127xSpi.set_rx_freq(freq)  # freq?
            SX127xSpi.set_mode("fsrx")
            return me.handled(me, event)

        elif sig == pq.Signal.TMOUT:
            return me.tran(me, SX127xSpiAhsm.receiving)

        return me.super(me, me.top)


    @staticmethod
    def receiving(me, event):
        """State HeyMac:receiving
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            SX127xSpi.set_op_mode(mode="rxonce")
        
        elif sig == pq.Signal.DIO0: # RX_DONE
            rx_time = event.value
            if SX127xSpi.check_rx_flags():
                payld, rssi, snr = SX127xSpi.get_rx()
                pkt_data = (rx_time, payld, rssi, snr)
                pq.Framework.publish(pq.Event(pq.Signal.RX_DATA, pkt_data))
            else:
                # TODO: crc error stats
                pass
            return me.tran(me, SX127xSpiAhsm.idling)

        elif sig == pq.Signal.DIO1: # RX_TIMEOUT
            return me.tran(me, SX127xSpiAhsm.idling)

        elif sig == pq.Signal.DIO3: # ValidHeader
            # TODO: future: DIO3  for earlier rx_time capture

        return me.super(me, me.top)


#### Transmit chain
    @staticmethod
    def tx_prepping(me, event):
        """State: HeyMac:idling:tx_prepping
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            tx_time, tx_data = event.value

            # Prepare DIO0 to cause TxDone interrupt
            SX127xSpiAhsm.set_dio_mapping(dio0=1)
            SX127xSpiAhsm.set_tx_data(tx_data)
            SX127xSpiAhsm.enable_irqs(SX127xSpiAhsm.IRQFLAGS_TXDONE_MASK)
            SX127xSpiAhsm.clear_irqs(SX127xSpiAhsm.IRQFLAGS_TXDONE_MASK)

            #TODO set timer to TX at appropriate time

            # Reminder pattern to trans to fstxing
            me.postFIFO(pq.Event(pq.Signal.ALWAYS, None))
            return me.handled(me, event)

        elif sig == pq.Signal.ALWAYS:
            return me.tran(me, SX127xSpiAhsm.fstxing)

        elif sig == pq.Signal.EXIT:
            return me.handled(me, event)

        return me.super(me, me.idling)


    @staticmethod
    def fstxing(me, event):
        """State: HeyMac:fstxing
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            SX127xSpi.set_mode("fstx")
            return me.handled(me, event)

        elif sig == pq.Signal.TMOUT:
            return me.tran(me, SX127xSpiAhsm.transmit)

        return me.super(me, me.top)


    @staticmethod
    def transmitting(me, event):
        """State: HeyMac:transmitting
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            SX127xSpi.set_mode("tx")
            return me.handled(me, event)

        elif sig == pq.Signal.DIO0: # TX_DONE
            return me.tran(me, SX127xSpiAhsm.idling)

        return me.super(me, me.top)

