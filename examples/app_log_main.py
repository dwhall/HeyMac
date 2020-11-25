#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Launches all the state machines to run the HeyMac network
"""

import logging
import socket
import sys

import farc
from farc.SimpleSpy import SimpleSpy
import heymac
from heymac import utl

#import prj_cfg
#import prj_stngs


def main():
    saddr = utl.get_long_mac_addr("KC4KSU")
    # The hostname is the station ID
    station_id = socket.gethostname().encode()

    # Instantiate state machines
    macAhsm = heymac.HeyMacCsmaAhsm(saddr, station_id)

    # Start state machines
    macAhsm.start_stack(50)

    farc.run_forever()


if __name__ == "__main__":
    if False:
        farc.Spy.enable_spy(SimpleSpy)
    else:
        logging.basicConfig(
            stream = sys.stdout,
            format = "%(asctime)s %(message)s",
            level = logging.INFO)

    main()
