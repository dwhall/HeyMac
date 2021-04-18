"""
Copyright 2017 Dean Hall.  See LICENSE for details.

Physical Layer State Machine for UART operations on the RasPi
- reads a UART, calls a callback to process data
"""


import farc

try:
    import serial
except ImportError:
    from . import mock_serial as serial

try:
    import RPi.GPIO as GPIO
except ImportError:
    from ..phy import mock_gpio as GPIO


class UartHsm(farc.Ahsm):

    _POLL_PERIOD = 0.100 # [secs]

    def __init__(self, rx_callback=None):
        super().__init__()
        self._rx_callback = rx_callback


    def open(self, port, baudrate):
        self._uart_stngs = {"port": port, "baudrate": baudrate, "timeout": 0}
        self.post_fifo(self._open_evt)


    def close(self):
        self.post_fifo(self._close_evt)


# State Machine

    @farc.Hsm.state
    def _initial(self, event):
        """Pseudostate: UartHsm:_initial"""

        farc.Signal.register("_UART_OPEN")
        farc.Signal.register("_UART_CLOSE")

        self._open_evt = farc.Event(farc.Signal._UART_OPEN, None)
        self._close_evt = farc.Event(farc.Signal._UART_CLOSE, None)
        self._tm_evt = farc.TimeEvent("_UART_TMOUT")

        return self.tran(UartHsm._ready)


    @farc.Hsm.state
    def _ready(self, event):
        """State: UartHsm:_ready"""
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return self.handled(event)

        elif sig == farc.Signal._UART_OPEN:
            return self.tran(UartHsm._running)

        elif sig == farc.Signal.SIGTERM:
            return self.tran(self._exiting)

        return self.super(self.top)


    @farc.Hsm.state
    def _running(self, event):
        """State: UartHsm:_running"""
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            self._uart_data = bytearray()
            self._ser = serial.Serial(**self._uart_stngs)
            self._read_size = round(1.5 * self._ser.baudrate * UartHsm._POLL_PERIOD)
            self._tm_evt.post_every(self, UartHsm._POLL_PERIOD)
            return self.handled(event)

        elif sig == farc.Signal._UART_TMOUT:
            self._uart_data.extend(self._ser.read(self._read_size))
            if self._rx_callback:
                self._rx_callback(self._uart_data)
            return self.handled(event)

        elif sig == farc.Signal._UART_CLOSE:
            return self.tran(self._ready)

        elif sig == farc.Signal.SIGTERM:
            return self.tran(self._exiting)

        elif sig == farc.Signal.EXIT:
            self._tm_evt.disarm()
            self._ser.close()
            return self.handled(event)

        return self.super(self.top)


    @farc.Hsm.state
    def _exiting(self, event):
        """State UartHsm:_exiting"""
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return self.handled(event)

        return self.super(self.top)


def parse_nmea(nmea_ba):
    """Callback to parse NMEA data for the UartHsm

    The caller must re-use nmea_ba to retain partial sentences.
    The caller must do this once: farc.Signal.register("GPS_GPRMC")
    """
    n = nmea_ba.find(b"\r\n")
    while n >= 0:
        nmea_sentence = bytes(nmea_ba[0:n])
        del nmea_ba[0:n+2]

        if nmea_sentence.startswith(b"$GPRMC"):
            farc.Framework.publish(farc.Event(farc.Signal.GPS_GPRMC, nmea_sentence.decode()))

        n = nmea_ba.find(b"\r\n")

    # Flush junk data or UART rate mismatch
    if n<0 and len(nmea_ba) >= 256:
        nmea_ba.clear()


class GpsHsm(UartHsm):
    _NMEA_BAUD = 9600

    def __init__(self, pps_pin, rx_callback=parse_nmea):
        super().__init__(rx_callback)
        self._pps_pin = pps_pin
        farc.Signal.register("GPS_GPRMC")
        farc.Signal.register("GPS_PPS")

    @farc.Hsm.state
    def _initial(self, event):
        retval = super()._initial(self, event)
        self._pps_evt = farc.Event(farc.Signal.GPS_PPS, None)
        GPIO.setmode(GPIO.BCM)
        return retval

    def open(self, port):
        super().open(port, GpsHsm._NMEA_BAUD)
        GPIO.setup(self._pps_pin, GPIO.IN)
        GPIO.add_event_detect(self._pps_pin, edge=GPIO.RISING, callback=self._pps_handler)

    def close(self):
        super().close()
        GPIO.remove_event_detect(self._pps_pin)

    def _pps_handler(self, chnl):
        assert chnl == 26
        farc.Framework.publish(self._pps_evt)
