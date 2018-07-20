#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Launches all the state machines to run the HeyMac network
"""

import asyncio
import logging
import pq
import socket
import sys

import mac_tdma_ahsm
import phy_gpio_ahsm
import phy_spi_ahsm
import phy_uart_ahsm


def main():
    # Instantiate state machines
    gpioAhsm = phy_gpio_ahsm.GpioAhsm(phy_gpio_ahsm.GpioAhsm.initial)
    spiAhsm = phy_spi_ahsm.SX127xSpiAhsm(phy_spi_ahsm.SX127xSpiAhsm.initial)
    uartAhsm = phy_uart_ahsm.UartAhsm(phy_uart_ahsm.UartAhsm.initial)
    macAhsm = mac_tdma_ahsm.HeyMacAhsm(mac_tdma_ahsm.HeyMacAhsm.initial)

    # Start state machines
    spiAhsm.start(10)
    gpioAhsm.start(20)
    uartAhsm.start(30)
    macAhsm.start(50)

    # Start event loop
    loop = asyncio.get_event_loop()
    loop.run_forever()
    loop.close()


if __name__ == "__main__":
    pq.Spy.enable_spy(pq.VcdSpy)

    # log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_fmt = "%(asctime)s %(message)s"
    logging.basicConfig(
            filename = __file__ + "." + socket.gethostname() + ".log",
            format = log_fmt,
            level = logging.INFO)

    # Also log to stdout
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(log_fmt))
    logging.getLogger().addHandler(ch)

    main()
