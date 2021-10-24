#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Runs the HeyMac stack with a text user interface.
"""

# import logging, sys

import farc

from heymac.lnk import HeymacCsmaHsm
from heymac.phy import SX127x, SX127xHsm, SpiConfig, DioConfig, ResetConfig
from heymac.utl import GpsHsm

from tui_hsm import TxtUiHsm


def main():
    # logging.basicConfig(
    #    filename="/home/pi/heymaclog.txt",
    #    format="%(asctime)s %(message)s",
    #    level=logging.DEBUG)

    # Init platform configuration and SX127x radio
    spi_cfg = SpiConfig(port=0, cs=0, freq=10_000_000)
    dio_cfg = DioConfig(4, 23, 24, 6, 5, 22)
    reset_cfg = ResetConfig(17)
    sx127x = SX127x(spi_cfg, dio_cfg, reset_cfg)

    phy_hsm = SX127xHsm(sx127x, True)
    lnk_hsm = HeymacCsmaHsm(phy_hsm)
    tui_hsm = TxtUiHsm(phy_hsm, lnk_hsm)
    gps_hsm = GpsHsm(pps_pin=26)

    lnk_hsm.start(50)
    phy_hsm.start(40)
    tui_hsm.start(30)
    gps_hsm.start(60)

    gps_hsm.open("/dev/serial0")

    farc.run_forever()


if __name__ == "__main__":
    main()
