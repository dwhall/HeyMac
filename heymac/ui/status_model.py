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
        s = bytearray(b"--------")

        # Set transmitter status
        if self.is_tx_restricted():
            s[0] = ord('x')
        elif self._phy_hsm._state == self._phy_hsm._txing:
            s[0] = ord('T')
        else:
            s[0] = ord('t')

        # Set receiver status
        if self._phy_hsm._state == self._phy_hsm._listening:
            s[1] = ord('L')
        elif self._phy_hsm._state == self._phy_hsm._rxing:
            s[1] = ord('R')
        elif self._phy_hsm._state == self._phy_hsm._initializing:
            pass
        else:
            s[1] = ord('x')

        return s.decode()
