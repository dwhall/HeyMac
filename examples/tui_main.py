#!/usr/bin/env python3

"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Runs the HeyMac stack with a text user interface.
"""

import farc

import lnk_heymac
import phy_sx127x
import tui_ahsm


def main():
    phy_sm = phy_sx127x.PhySX127xAhsm(True)
    lnk_sm = lnk_heymac.LnkHeymacCsmaAhsm(phy_sm)
    tui_sm = tui_ahsm.TxtUiAhsm(phy_sm, lnk_sm)

    lnk_sm.start(50)
    phy_sm.start(40)
    tui_sm.start(30)

    farc.run_forever()


if __name__ == "__main__":
    main()
