#!/usr/bin/env python3

"""
Copyright 2019 Dean Hall.  See LICENSE for details.

Launches all the state machines to run the HeyMac network
"""

import asyncio
import socket
import sys

import farc
import heymac

import prj_cfg


def main():
    # Instantiate state machines
    gpioAhsm = heymac.GpioAhsm()
    spiAhsm = heymac.SX127xSpiAhsm()
    uartAhsm = heymac.UartAhsm()
    macAhsm = heymac.HeyMacAhsm()

    # Register GPIO inputs to emit signals
    for pin_nmbr, pin_edge, sig_name in prj_cfg.gpio_ins:
        gpioAhsm.register_pin_in(pin_nmbr, pin_edge, sig_name)
#    for pin_nmbr, pin_initial in prj_cfg.gpio_outs:
#        gpioAhsm.register_pin_out(pin_nmbr, pin_initial)

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
    main()