#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Runs the HeyMac stack with a text user interface.
"""

import farc

from heymac.lnk import HeymacCsmaHsm
from heymac.phy import SX127xHsm
from tui_hsm import TxtUiHsm


def main():
    phy_sm = SX127xHsm(True)
    lnk_sm = HeymacCsmaHsm(phy_sm)
    tui_sm = TxtUiHsm(phy_sm, lnk_sm)

    lnk_sm.start(50)
    phy_sm.start(40)
    tui_sm.start(30)

    farc.run_forever()


if __name__ == "__main__":
    main()
