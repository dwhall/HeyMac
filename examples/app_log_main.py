#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Launches all the state machines to run the HeyMac network
"""

import logging
import socket
import sys

import farc
import heymac
from heymac import utl

#import prj_cfg
#import prj_stngs


def main():
    saddr = utl.get_long_mac_addr("KC4KSU")
    # The hostname is the station ID
    station_id = socket.gethostname().encode()

    # Instantiate state machines
#    gpioAhsm = heymac.GpioAhsm()
#    spiAhsm = heymac.SX127xSpiAhsm(prj_stngs.spi_stngs, prj_stngs.modem_stngs)
#    spiAhsm = heymac.PhySX127xAhsm(prj_cfg.spi_cfg, prj_cfg.dio_cfg, prj_cfg.reset_cfg)
#    uartAhsm = heymac.UartAhsm(heymac.parse_nmea)
    macAhsm = heymac.HeyMacCsmaAhsm(saddr, station_id)

    # Register GPIO inputs to emit signals
#    for pin_nmbr, pin_edge, sig_name in prj_cfg.gpio_ins:
#        gpioAhsm.register_pin_in(pin_nmbr, pin_edge, sig_name)
#    for pin_nmbr, pin_initial in prj_cfg.gpio_outs:
#        gpioAhsm.register_pin_out(pin_nmbr, pin_initial)

    # Start state machines
#    spiAhsm.start(10)
#    gpioAhsm.start(20)
#   uartAhsm.start(30)
    macAhsm.start_stack(50)

    # Open the UART to process NMEA
#    uartAhsm.post_open(prj_cfg.uart_cfg)

    farc.run_forever()


if __name__ == "__main__":
    logging.basicConfig(
        stream = sys.stdout,
        format = "%(asctime)s %(message)s",
        level = logging.INFO)

    main()
