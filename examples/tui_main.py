#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Runs the HeyMac stack with a text user interface.
"""

#import logging, sys

import farc

from heymac.lnk import HeymacCsmaHsm
from heymac.phy import SX127xHsm
from heymac.utl import HamIdent

from tui_hsm import TxtUiHsm


def main():
    #logging.basicConfig(
    #    stream=sys.stdout,
    #    format="%(asctime)s %(message)s",
    #    level=logging.INFO)

    phy_hsm = SX127xHsm(True)
    lnk_hsm = HeymacCsmaHsm(phy_hsm, HamIdent)
    tui_hsm = TxtUiHsm(phy_hsm, lnk_hsm)

    lnk_hsm.start(50)
    phy_hsm.start(40)
    tui_hsm.start(30)

    farc.run_forever()


if __name__ == "__main__":
    main()
