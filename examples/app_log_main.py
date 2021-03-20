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
import lnk_heymac
import phy_sx127x
import tui_ahsm


def main():
    logging.basicConfig(
        stream=sys.stdout,
        format="%(asctime)s %(message)s",
        level=logging.DEBUG)

    # Compute the long address from host credentials
    station_id = socket.gethostname()
    lnk_addr = heymac.utl.get_long_addr(station_id)

    # Instantiate state machines
    phy_sm = phy_sx127x.PhySX127xAhsm(True)
    lnk_sm = lnk_heymac.LnkHeymacCsmaAhsm(phy_sm, lnk_addr, station_id)
    tui_sm = tui_ahsm.TxtUiAhsm(phy_sm, lnk_sm)

    # Start state machines with their priorities
    lnk_sm.start(50)
    phy_sm.start(40)
    tui_sm.start(30)

    farc.run_forever()


if __name__ == "__main__":
    main()
