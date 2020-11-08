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
    def _initial(self, event):
        """Pseudostate: UartAhsm:_initial
        """
        # Incoming signals
        farc.Signal.register("PHY_UART_OPEN") # Value is serial.Serial() parameters
        farc.Signal.register("PHY_UART_CLOSE") # No value

        # Initialize a timer to perform polling
        self.tm_evt = farc.TimeEvent("_PHY_UART_TM_EVT")

        return self.tran(UartAhsm._ready)


    @farc.Hsm.state
    def _ready(self, event):
        """State: UartAhsm:_ready
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return self.handled(event)

        elif sig == farc.Signal.PHY_UART_OPEN:
            # TODO: if value is None: use default uart params
            self.uart_stngs = event.value
            return self.tran(UartAhsm._running)

        elif sig == farc.Signal.SIGTERM:
            return self.tran(self._exiting)

        return self.super(self.top)


    @farc.Hsm.state
    def _running(self, event):
        """State: UartAhsm:_running
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:

            # Init the data buffer
            self.uart_data = bytearray()

            # Open the port with the given argument.
            # expecting a dict like this:
            #   {"port":<uart port string>, "baudrate":<baud rate int>, "timeout"=0}
            self.ser = serial.Serial(**self.uart_stngs)

            # Start the polling timer
            self.tm_evt.post_every(self, UartAhsm.UART_POLL_PERIOD)
            return self.handled(event)

        elif sig == farc.Signal._PHY_UART_TM_EVT:
            # UART buffer size depends on baud rate (2X for margin)
            ser_fifo_max = 2 * round(self.ser.baudrate * UartAhsm.UART_POLL_PERIOD)

            # Read the available data from the serial port
            new_bytes = self.ser.read(ser_fifo_max)
            if len(new_bytes):
                self.uart_data.extend(new_bytes)

                # Pass data to callback. uart_data is modified in-place
                # by the callback; we must persist uart_data here
                if self.rx_callback:
                    self.rx_callback(self.uart_data)
            return self.handled(event)

        elif sig == farc.Signal.PHY_UART_CLOSE:
            return self.tran(self._ready)

        elif sig == farc.Signal.SIGTERM:
            return self.tran(self._exiting)

        elif sig == farc.Signal.EXIT:
            self.tm_evt.disarm()
            self.ser.close()
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _exiting(self, event):
        """State UartAhsm:_exiting
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return self.handled(event)

        return self.super(self.top)

    # Public interface
    def post_open(self, stngs):
        """Posts the OPEN event to self with the given settings
        """
        # TODO: validate settings
        self.post_fifo(farc.Event(farc.Signal.PHY_UART_OPEN, stngs))


    def post_close(self):
        """Posts the CLOSE event to self
        """
        self.post_fifo(farc.Event(farc.Signal.PHY_UART_close))
