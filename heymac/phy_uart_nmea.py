#!/usr/bin/env python3
"""
Copyright 2019 Dean Hall.  See LICENSE for details.

Physical Layer operations to process NMEA data from the UART.
- provides a callback for received UART data
- parses NMEA sentences and posts them as PHY_GPS_NMEA events
"""


import farc


def parse_nmea(nmea_ba):
    """Parses the nmea_ba bytearray containing NMEA data.
    Uses \r\n as a line delimiter and publishes $GPRMC sentences.
    Affects the contents of the caller's nmea_ba by reference
    (i.e. some data may be consumed from nmea_ba
    and incomplete data may remain in nmea_ba.
    The caller must re-use the same object each tme parse_nmea
    is called in order to persist partial data).
    """
    # Check if there is an end-of-sentence
    n = nmea_ba.find(b"\r\n")
    while n >= 0:

        # Create an immutable bytes object from the data (include delimiter)
        nmea_sentence = bytes(nmea_ba[0:n + 2])

        # Keep any data from after the delimiter
        nmea_ba = nmea_ba[n+2:]

        # Publish a full $GPRMC sentence
        if nmea_sentence.startswith(b"$GPRMC"):
            farc.Framework.publish(farc.Event(farc.Signal.PHY_GPS_NMEA, nmea_sentence))

        # Check for another sentence
        n = nmea_ba.find(b"\r\n")

    # If there are no newlines and the buffer is getting big, flush the junk data.
    # This protects against accumulating data that isn't NMEA or
    # is junk due to a UART data rate mismatch
    if n<0 and len(nmea_ba) >= 256:
        nmea_ba.clear()
