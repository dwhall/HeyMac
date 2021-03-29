#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Runs the HeyMac stack with a text user interface.
"""

import farc

from heymac.lnk_heymac import LnkHeymacCsmaAhsm
from heymac.phy_sx127x import PhySX127xAhsm
from tui_ahsm import TxtUiAhsm


def main():
    phy_sm = PhySX127xAhsm(True)
    lnk_sm = LnkHeymacCsmaAhsm(phy_sm)
    tui_sm = TxtUiAhsm(phy_sm, lnk_sm)

    lnk_sm.start(50)
    phy_sm.start(40)
    tui_sm.start(30)

    farc.run_forever()


if __name__ == "__main__":
    main()
