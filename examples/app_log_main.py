#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Launches all the state machines to run the HeyMac network
"""

import asyncio
import logging
import socket
import sys

import farc

import heymac


def main():
    # Instantiate state machines
    gpioAhsm = heymac.GpioAhsm(heymac.GpioAhsm.initial)
    spiAhsm = heymac.SX127xSpiAhsm(heymac.SX127xSpiAhsm.initial)
    uartAhsm = heymac.UartAhsm(heymac.UartAhsm.initial)
    macAhsm = heymac.HeyMacAhsm(heymac.HeyMacAhsm.initial)

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
    farc.Spy.enable_spy(farc.VcdSpy)

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
