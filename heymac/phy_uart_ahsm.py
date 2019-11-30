#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.

Physical Layer State Machine for UART operations on the RasPi
- reads a UART, calls a callback to process data

NOTE: This AHSM does not TX data at this time.
"""


import farc

try:
    import serial
except:
    from . import mock_serial as serial



class UartAhsm(farc.Ahsm):
    # Time period to check UART for data
    UART_POLL_PERIOD = 0.100 # [secs]

    def __init__(self, rx_callback=None):
        super().__init__()
        self.rx_callback = rx_callback


    @farc.Hsm.state
    def _initial(me, event):
        """Pseudostate: UartAhsm:_initial
        """
        # Incoming signals
        farc.Signal.register("PHY_UART_OPEN") # Value is serial.Serial() parameters
        farc.Signal.register("PHY_UART_CLOSE") # No value

        # Initialize a timer to perform polling
        me.tm_evt = farc.TimeEvent("_PHY_UART_TM_EVT")

        return me.tran(me, UartAhsm._ready)


    @farc.Hsm.state
    def _ready(me, event):
        """State: UartAhsm:_ready
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return me.handled(me, event)

        elif sig == farc.Signal.PHY_UART_OPEN:
            # TODO: if value is None: use default uart params
            me.uart_stngs = event.value
            return me.tran(me, UartAhsm._running)

        elif sig == farc.Signal.SIGTERM:
            return me.tran(me, me._exiting)

        return me.super(me, me.top)


    @farc.Hsm.state
    def _running(me, event):
        """State: UartAhsm:_running
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:

            # Init the data buffer
            me.uart_data = bytearray()

            # Open the port with the given argument.
            # expecting a dict like this:
            #   {"port":<uart port string>, "baudrate":<baud rate int>, "timeout"=0}
            me.ser = serial.Serial(**me.uart_stngs)

            # Start the polling timer
            me.tm_evt.postEvery(me, UartAhsm.UART_POLL_PERIOD)
            return me.handled(me, event)

        elif sig == farc.Signal._PHY_UART_TM_EVT:
            # UART buffer size depends on baud rate (2X for margin)
            ser_fifo_max = 2 * round(me.ser.baudrate * UartAhsm.UART_POLL_PERIOD)

            # Read the available data from the serial port
            me.uart_data.extend(me.ser.read(ser_fifo_max))

            # Pass data to callback. uart_data is modified in-place
            # by the callback; we must persist uart_data here
            if me.rx_callback:
                me.rx_callback(me.uart_data)
            return me.handled(me, event)

        elif sig == farc.Signal.PHY_UART_CLOSE:
            return me.tran(me, me._ready)

        elif sig == farc.Signal.SIGTERM:
            return me.tran(me, me._exiting)

        elif sig == farc.Signal.EXIT:
            me.tm_evt.disarm()
            me.ser.close()
            return me.handled(me, event)

        return me.super(me, me.top)


    @farc.Hsm.state
    def _exiting(me, event):
        """State UartAhsm:_exiting
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return me.handled(me, event)

        return me.super(me, me.top)

    # Public interface
    def post_open(self, stngs):
        """Posts the OPEN event to self with the given settings
        """
        # TODO: validate settings
        self.postFIFO(farc.Event(farc.Signal.PHY_UART_OPEN, stngs))


    def post_close(self):
        """Posts the CLOSE event to self
        """
        self.postFIFO(farc.Event(farc.Signal.PHY_UART_close))
