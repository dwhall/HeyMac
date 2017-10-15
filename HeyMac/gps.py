#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE file for details.
"""

import asyncio, logging
logging.basicConfig(filename=__file__+'.log',level=logging.INFO)
#logging.basicConfig(level=logging.INFO)

try:
    import serial
except ModuleNotFoundError:
    import mock_serial as serial

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    import mock_gpio as GPIO

import pq


GPS_NMEA_PERIOD = 0.100 # [secs]
SER_FIFO_MAX = 4095
## Connect GPS modules PPS pin 6 to RPi GPIO26 pin 37

class GpsAhsm(pq.Ahsm):
    """GPS Receiver State Machine
    Handles serial I/O to a GPS receiver
    and a GPIO pin for the Pulse Per Second (PPS).
    """

    def _pps_handler(self, chnl):
        """This is the PPS signal handler method
        that is called on a separate thread by the GPIO system.
        Publishes the PPS event and returns to the main thread.
        """
        pq.Framework.publish(self.evt_pps)


    @staticmethod
    def initial(me, event):
        """Pseudostate: GpsAhsm:initial
        """
        GPIO.setmode(GPIO.BCM)

        # Incoming signals
        pq.Framework.subscribe("GPS_PPS", me)
#        pq.Signal.register("GPS_OPEN") # Value is GPIO/BCM of PPS pin input

        # Outgoing signals
        pq.Signal.register("GPS_NMEA") # Value is one NMEA sentence [bytes]

        # Events of outgoing signals
        me.evt_pps = pq.Event(pq.Signal.register("GPS_PPS"), None)

        # Initialize a timer event used to schedule the NMEA handler
        me.te_nmea = pq.TimeEvent("GPS_NMEA_PRDC")
#        return me.tran(me, GpsAhsm.awaiting)
# Instrumenting
        me.ser_port = "/dev/serial0"
        me.pps_chnl = 26
        return me.tran(me, GpsAhsm.running)


    @staticmethod
    def awaiting(me, event):
        """State: GpsAhsm:Awaiting
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            logging.info("GpsAhsm Awaiting")
            return me.handled(me, event)

        elif sig == pq.Signal.GPS_OPEN:
            # Get the arguments from the msg
            # and transition to the Running state
            me.pps_chnl, me.ser_port = sig.value
            return me.tran(me, me.running)

        elif sig == pq.Signal.SIGTERM:
            logging.info("Received SIGTERM")
            return me.tran(me, me.exiting)

        return me.super(me, me.top)


    @staticmethod
    def running(me, event):
        """State: GpsAhsm:Running
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            logging.info("GpsAhsm Running")

            # Initialize a GPIO pin as an input for the PPS signal
            # and set the handler function for the signal
            GPIO.setup(me.pps_chnl, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.add_event_detect(me.pps_chnl, edge=GPIO.RISING, callback=me._pps_handler)

            # Init the NMEA data buffer
            me.nmea_data = bytearray()

            # Open the serial port where NMEA input is expected
            me.ser = serial.Serial(port=me.ser_port, baudrate=9600, timeout=0)

            # Start the repeating timer event
            me.te_nmea.postEvery(me, GPS_NMEA_PERIOD)
            return me.handled(me, event)

        elif sig == pq.Signal.GPS_NMEA_PRDC:
            # Read the available data from the serial port
            me.nmea_data.extend(me.ser.read(SER_FIFO_MAX))

            # If a newline is present, publish one or more NMEA sentences
            n = me.nmea_data.find(b"\r\n")
            while n >= 0:
                nmea_sentence = me.nmea_data[0:n+2]
                me.nmea_data = me.nmea_data[n+2:]
                pq.Framework.publish(pq.Event(pq.Signal.GPS_NMEA, nmea_sentence))
                if b"GPRMC" in nmea_sentence: 
                    logging.info("GPS_NMEA:" + str(nmea_sentence))
                n = me.nmea_data.find(b"\r\n")
            return me.handled(me, event)

        elif sig == pq.Signal.GPS_PPS:
            logging.info("GPS_PPS")
            return me.handled(me, event)

        elif sig == pq.Signal.SIGTERM:
            logging.info("Received SIGTERM")
            return me.tran(me, me.exiting)

        elif sig == pq.Signal.EXIT:
            me.te_nmea.disarm()
            me.ser.close()
            GPIO.setmode(GPIO.BCM)
            GPIO.cleanup(me.pps_chnl)
            me.pps_chnl = None
            return me.handled(me, event)

        return me.super(me, me.top)


    @staticmethod
    def exiting(me, event):
        """State GpsAhsm:exiting
        """
        sig = event.signal
        if sig == pq.Signal.ENTRY:
            print("GpsAhsm Exiting")
            return me.handled(me, event)
        
        # Tran back to awaiting
        return me.super(me, me.top)


if __name__ == "__main__":
    gps = GpsAhsm(GpsAhsm.initial)
    gps.start(0)

    loop = asyncio.get_event_loop()
    loop.run_forever()
    loop.close()
