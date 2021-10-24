"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Heymac Radio Status model.
"""


class StatusModel():
    def __init__(self, phy_hsm, lnk_hsm):
        self._phy_hsm = phy_hsm
        self._lnk_hsm = lnk_hsm


    def is_tx_restricted(self):
        return self._lnk_hsm._state in (self._lnk_hsm._lurking,
                                        self._lnk_hsm._initializing)


    def get_summary(self):
        return "--------"
