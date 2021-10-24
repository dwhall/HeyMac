"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Heymac Radio Status model.
"""


class StatusModel():
    def __init__(self, phy_hsm, lnk_hsm):
        self._phy_hsm = phy_hsm
        self._lnk_hsm = lnk_hsm


    def get_summary(self):
        return "--------"
