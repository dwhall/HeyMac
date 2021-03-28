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
    #callsign_ssid = "KC4KSU-999"
    #lnk_addr = heymac.utl.ham_ident.HamIdent.get_long_addr("HeyMac", callsign_ssid)

    # Instantiate state machines
    phy_sm = phy_sx127x.PhySX127xAhsm(True)
    lnk_sm = lnk_heymac.LnkHeymacCsmaAhsm(phy_sm)
    tui_sm = tui_ahsm.TxtUiAhsm(phy_sm, lnk_sm)

    # Start state machines with their priorities
    lnk_sm.start(50)
    phy_sm.start(40)
    tui_sm.start(30)

    farc.run_forever()


if __name__ == "__main__":
    main()
