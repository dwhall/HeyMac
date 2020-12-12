"""Copyright 2020 Dean Hall.  See LICENSE for details.
"""


from . import lnk_csma_ahsm
from . import lnk_frame
from . import lnk_heymac_cmd


class LnkData(object):
    """Heymac link layer data.

    Keeps neighbor data from received Heymac frames.
    Neighbor list holds data for each neighbor:
    - long addr
    - time of last rx (to know when to drop ngbr)
    - rx link Q (some func of recent rssi or snr)
    - latest beacon
    """
    def __init__(self,):
        self.ngbr_list = {}


    def process_bcn(self, frame):
        """Process a Heymac beacon and keeps relevant link data."""
        addr = frame.get_field(lnk_frame.HeymacFrame.FLD_SADDR)
        if addr not in self.ngbr_list:
            self.ngbr_list[addr] = {"BCN_CNT": 0}
        # TODO: create and use _NGBR_FLD_* names
        self.ngbr_list[addr]["BCN_FRAME"] = frame
        self.ngbr_list[addr]["BCN_CNT"] += 1

        # TODO: process nets[] to build list of known nets


    def ngbr_hears_me(self,):
        """Does a neighbor node hear this node.

        Returns True if at least one neighbor has this node
        in its neighbor list.  This proves two-way transmission
        has taken place.
        """
        for _, data in self.ngbr_list.items():
            # TODO: parse ngbrs[] for own address
            # return True
            pass
        return False


# Private


    # If we don't hear a neighbor (or periodic item)
    # for this many seconds then consider it expired/invalid
    # FIXME: circular dependency:
    # _EXPIRATION_PRD = 4 * lnk_csma_ahsm.LnkHeymac._BCN_PRD

