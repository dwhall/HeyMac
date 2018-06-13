#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE for details.

Physical Layer State Machine for UART operations on the RasPi
- reads a UART, parses NMEA sentences and posts them as GPS_NMEA events
"""


import serial

import pq


# TODO: move to config file
uart_port = "/dev/serial0"
uart_baud = 9600

# Time period to check UART for NMEA data
GPS_NMEA_PERIOD = 0.100 # [secs]

# UART buffer size depends on baud rate (2X for margin)
SER_FIFO_MAX = 2 * round(uart_baud * GPS_NMEA_PERIOD)


class UartAhsm(pq.Ahsm):

    @staticmethod
    def initial(me, event):
        """Pseudostate: UartAhsm:initial
        """
        # Outgoing signals
        pq.Signal.register("GPS_NMEA") # Value is one NMEA sentence [bytes]

        # Initialize a timer event used to schedule the NMEA handler
        me.te_nmea = pq.TimeEvent("GPS_NMEA_PRDC")

        return me.tran(me, UartAhsm.running)


    @staticmethod
    def running(me, event):
        """State: UartAhsm:Running
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:

            # Init the NMEA data buffer
            me.nmea_data = bytearray()

            # Open the port where NMEA input is expected
            me.ser = serial.Serial(port=uart_port, baudrate=uart_baud, timeout=0)

            # Start the repeating timer event
            me.te_nmea.postEvery(me, GPS_NMEA_PERIOD)
            return me.handled(me, event)

        elif sig == pq.Signal.GPS_NMEA_PRDC:
            # Read the available data from the serial port
            me.nmea_data.extend(me.ser.read(SER_FIFO_MAX))

            # If a newline is present, publish one or more NMEA sentences
            n = me.nmea_data.find(b"\r\n")
            while n >= 0:
                nmea_sentence = bytes(me.nmea_data[0:n+2])
                me.nmea_data = me.nmea_data[n+2:]
                if b"GPRMC" in nmea_sentence:
                    pq.Framework.publish(pq.Event(pq.Signal.GPS_NMEA, nmea_sentence))
                n = me.nmea_data.find(b"\r\n")
            return me.handled(me, event)

        elif sig == pq.Signal.SIGTERM:
            return me.tran(me, me.exiting)

        elif sig == pq.Signal.EXIT:
            me.te_nmea.disarm()
            me.ser.close()
            return me.handled(me, event)

        return me.super(me, me.top)


    @staticmethod
    def exiting(me, event):
        """State UartAhsm:exiting
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            return me.handled(me, event)

        return me.super(me, me.top)


