#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Launches all the state machines to run the HeyMac network
"""

import logging
import sys

import farc
import heymac

import prj_cfg


def main():
    # Register signal for app-specific UART callback
    farc.Signal.register("PHY_GPS_NMEA")

    # Instantiate state machines
    gpioAhsm = heymac.GpioAhsm()
    spiAhsm = heymac.SX127xSpiAhsm()
    uartAhsm = heymac.UartAhsm(heymac.parse_nmea)
    macAhsm = heymac.HeyMacAhsm()

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
    uartAhsm.postFIFO(farc.Event(farc.Signal.PHY_UART_OPEN, uart_stngs))

    farc.run_forever()


if __name__ == "__main__":
    logging.basicConfig(
        stream = sys.stdout,
        format = "%(asctime)s %(message)s",
        level = logging.INFO)

    main()
