#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Launches all the state machines to run the HeyMac network
"""

import hashlib
import logging
import socket
import sys

import farc
import heymac
from heymac import utl

import prj_cfg
import prj_stngs


def main():
    # Register signal for app-specific UART callback
    farc.Signal.register("PHY_GPS_NMEA")

    # Turn user JSON config files into Python dicts
    mac_identity = utl.get_from_json("HeyMac", "mac_identity.json")
    # Convert hex bytes to bytearray since JSON can't do binary strings
    pub_key = bytearray.fromhex(mac_identity['pub_key'])
    # Calculate the 128-bit source address from the identity's pub_key
    h = hashlib.sha512()
    h.update(pub_key)
    h.update(h.digest())
    saddr = h.digest()[:8]
    assert saddr[0] in (0xfc, 0xfd)

    # The hostname is the station ID
    station_id = socket.gethostname().encode()

    # Instantiate state machines
    gpioAhsm = heymac.GpioAhsm()
    spiAhsm = heymac.SX127xSpiAhsm(prj_stngs.spi_stngs, prj_stngs.lora_stngs)
    uartAhsm = heymac.UartAhsm(heymac.parse_nmea)
    macAhsm = heymac.HeyMacCsmaAhsm(saddr, station_id)

    # Register GPIO inputs to emit signals
    for pin_nmbr, pin_edge, sig_name in prj_cfg.gpio_ins:
        gpioAhsm.register_pin_in(pin_nmbr, pin_edge, sig_name)
    for pin_nmbr, pin_initial in prj_cfg.gpio_outs:
        gpioAhsm.register_pin_out(pin_nmbr, pin_initial)

    # Start state machines
    spiAhsm.start(10)
    gpioAhsm.start(20)
    uartAhsm.start(30)
    macAhsm.start(50)

    # Open the UART to process NMEA
    uart_stngs = {
        "port": "/dev/serial0",
        "baudrate": 9600,
        "timeout": 0,
    }
    uartAhsm.post_open(uart_stngs)

    farc.run_forever()


if __name__ == "__main__":
    logging.basicConfig(
        stream = sys.stdout,
        format = "%(asctime)s %(message)s",
        level = logging.INFO)

    main()
