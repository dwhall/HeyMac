#!/usr/bin/env python3
"""
Copyright 2017 Dean Hall.  See LICENSE file for details.
"""


class GpsCfg(object):
    pass


class DraginoLoraGpsHat(GpsCfg):
    # PCB version 1.3
    # WIRING REQUIREMENT: connect GPS module's PPS pin 6 to RPi's GPIO26 pin 37
    serial_port = "/dev/serial0"
    serial_baud = 9600
    pps_chnl    = 26
