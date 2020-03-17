#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Launches all the state machines to run the HeyMac network
"""


import asyncio
import logging
import socket
logging.basicConfig(
        filename = __file__ + "." + socket.gethostname() + ".log",
        format = "%(asctime)s %(message)s",
        level = logging.INFO)

import heymac
from heymac import utl

import app_chat_ahsm
import prj_cfg
import prj_stngs


def main():
    saddr = utl.get_long_mac_addr("KC4KSU")
    # The hostname is the station ID
    station_id = socket.gethostname().encode()

    # Instantiate state machines
    gpioAhsm = heymac.GpioAhsm()
    spiAhsm = heymac.SX127xSpiAhsm(prj_stngs.spi_stngs, prj_stngs.modem_stngs)
    uartAhsm = heymac.UartAhsm()
    macAhsm = heymac.HeyMacCsmaAhsm(saddr, station_id)
    chatAhsm = app_chat_ahsm.ChatAhsm()

    # Configure GPIO
    for pin_nmbr, pin_edge, sig_name in prj_cfg.gpio_ins:
        gpioAhsm.register_pin_in(pin_nmbr, pin_edge, sig_name)
#    for pin_nmbr, pin_initial in prj_cfg.gpio_outs:
#        gpioAhsm.register_pin_out(pin_nmbr, pin_initial)

    # Start state machines (with priorities)
    spiAhsm.start(10)
    gpioAhsm.start(20)
    uartAhsm.start(30)
    macAhsm.start(50)
    chatAhsm.start(70)

    # Start event loop
    loop = asyncio.get_event_loop()
    loop.run_forever()
    loop.close()

if __name__ == "__main__":
    main()
