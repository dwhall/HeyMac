#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Launches all the state machines to run the HeyMac network
"""

import logging
import socket
import sys

import farc
import farc.SimpleSpy
import heymac
#from heymac import utl
import lnk_heymac


def main():
    if False:
        farc.Spy.enable_spy(farc.SimpleSpy)
    else:
        logging.basicConfig(
            stream = sys.stdout,
            format = "%(asctime)s %(message)s",
            level = logging.DEBUG)

    lnk_addr = heymac.utl.get_long_mac_addr("KC4KSU")
    # The hostname is the station ID
    station_id = socket.gethostname().encode()

    # Instantiate state machines
    lnk_ahsm = lnk_heymac.LnkHeymacCsmaAhsm(lnk_addr, station_id)

    # Start state machines
    lnk_ahsm.start_stack(50)

    farc.run_forever()


if __name__ == "__main__":
    main()
