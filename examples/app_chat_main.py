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

import app_chat_ahsm
import prj_cfg


def main():
    # Instantiate state machines
    gpioAhsm = heymac.phy_gpio_ahsm.GpioAhsm(heymac.phy_gpio_ahsm.GpioAhsm.initial)
    spiAhsm = heymac.phy_sx127x_ahsm.SX127xSpiAhsm(heymac.phy_sx127x_ahsm.SX127xSpiAhsm.initial)
    uartAhsm = heymac.phy_uart_ahsm.UartAhsm(heymac.phy_uart_ahsm.UartAhsm.initial)
    macAhsm = heymac.mac_tdma_ahsm.HeyMacAhsm(heymac.mac_tdma_ahsm.HeyMacAhsm.initial)
    chatAhsm = app_chat_ahsm.ChatAhsm(app_chat_ahsm.ChatAhsm.initial)

    # Configure GPIO
    for pin_nmbr, pin_edge, sig_name in prj_cfg.gpio_ins:
        gpioAhsm.register_pin_in(pin_nmbr, pin_edge, sig_name)
    for pin_nmbr, pin_initial in prj_cfg.gpio_outs:
        gpioAhsm.register_pin_out(pin_nmbr, pin_initial)

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
