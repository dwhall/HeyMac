#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.

Physical Layer State Machine for UART operations on the RasPi
- reads a UART, parses NMEA sentences and posts them as PHY_GPS_NMEA events
"""


import sys

import farc

if sys.platform == "linux":
    import serial
else:
    from . import mock_serial as serial

from . import phy_cfg


# Time period to check UART for NMEA data
GPS_NMEA_PERIOD = 0.100 # [secs]

# UART buffer size depends on baud rate (2X for margin)
SER_FIFO_MAX = 2 * round(phy_cfg.uart_baud * GPS_NMEA_PERIOD)


class UartAhsm(farc.Ahsm):

    @farc.Hsm.state
    def initial(me, event):
        """Pseudostate: UartAhsm:initial
        """
        # Outgoing signals
        farc.Signal.register("PHY_GPS_NMEA") # Value is one NMEA sentence [bytes]

        # Initialize a timer event used to schedule the NMEA handler
        me.tm_evt = farc.TimeEvent("_PHY_UART_TM_EVT")

        return me.tran(me, UartAhsm.running)


    @farc.Hsm.state
    def running(me, event):
        """State: UartAhsm:Running
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:

            # Init the NMEA data buffer
            me.nmea_data = bytearray()

            # Open the port where NMEA input is expected
            me.ser = serial.Serial(port=phy_cfg.uart_port, baudrate=phy_cfg.uart_baud, timeout=0)

            # Start the repeating timer event
            me.tm_evt.postEvery(me, GPS_NMEA_PERIOD)
            return me.handled(me, event)

        elif sig == farc.Signal._PHY_UART_TM_EVT:
            # Read the available data from the serial port
            me.nmea_data.extend(me.ser.read(SER_FIFO_MAX))

            # If a newline is present, publish one or more NMEA sentences
            n = me.nmea_data.find(b"\r\n")
            if n >= 0:
                while n >= 0:
                    nmea_sentence = bytes(me.nmea_data[0:n+2])
                    me.nmea_data = me.nmea_data[n+2:]
                    if b"GPRMC" in nmea_sentence:
                        farc.Framework.publish(farc.Event(farc.Signal.PHY_GPS_NMEA, nmea_sentence))
                    n = me.nmea_data.find(b"\r\n")

            # If there are no newlines and the buffer is getting big, flush the junk data
            elif len(me.nmea_data) >= 256:
                me.nmea_data.clear()

            return me.handled(me, event)

        elif sig == farc.Signal.SIGTERM:
            return me.tran(me, me.exiting)

        elif sig == farc.Signal.EXIT:
            me.tm_evt.disarm()
            me.ser.close()
            return me.handled(me, event)

        return me.super(me, me.top)


    @farc.Hsm.state
    def exiting(me, event):
        """State UartAhsm:exiting
        """
        sig = event.signal
        if sig == farc.Signal.ENTRY:
            return me.handled(me, event)

        return me.super(me, me.top)
