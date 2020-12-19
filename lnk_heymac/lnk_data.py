"""Copyright 2020 Dean Hall.  See LICENSE for details.
"""


import farc

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
    def __init__(self, lnk_addr):
        self._lnk_addr = lnk_addr
        self._ngbr_list = {}


    def get_ngbrs_lnk_addrs(self,):
        """Returns a list of neighbors' link addresses."""
        return self._ngbr_list.keys()


    def get_ngbrs_nets(self,):
        """Returns a list of neighbors' net data.

        Net data is a tuple of the net_id as a bytes object
        and the link address of the network's root (also a bytes object).
        """
        nets = set()
        for data in self._ngbr_list.values():
            frame = data["BCN_FRAME"]
            for net in frame.get_field(HeymacCmd.FLD_NETS):
                nets.add(net)
        return list(nets)


    def ngbr_hears_me(self,):
        """Does a neighbor node hear this node.

        Returns True if at least one neighbor has this node
        in its neighbor list.  This proves two-way transmission
        has taken place.
        """
        for data in self._ngbr_list.values():
            frame = data["BCN_FRAME"]
            bcn = frame.cmd
            assert type(bcn) is lnk_heymac_cmd.HeymacCmdCsmaBcn
            ngbrs = bcn.get_field(lnk_heymac_cmd.HeymacCmd.FLD_NGBRS)
            return self._lnk_addr in ngbrs
        return False


    def process_frame(self, frame):
        """Update link data with info from the given frame."""
        assert type(frame) is lnk_frame.HeymacFrame

        # TODO: update link quality using any frame

        # Process a beacon
        if frame.cmd and type(frame.cmd) is lnk_heymac_cmd.HeymacCmdCsmaBcn:
            self._process_bcn(frame)


    def update(self,):
        """Performs periodic update of the link data."""
        now = farc.Framework._event_loop.time()
        # Collect and prune expired neighbors
        expired_ngbrs = []
        for ngbr_addr, data in self._ngbr_list.items():
            frame = data["BCN_FRAME"]
            rx_time = frame.rx_meta[0]
            if now > rx_time + self._EXPIRATION_PRD:
                expired_ngbrs.append(ngbr_addr)
        for ngbr_addr in expired_ngbrs:
            del self._ngbr_list[ngbr_addr]


# Private


    # If we don't hear a neighbor (or periodic item)
    # for this many seconds then consider it expired/invalid
    # FIXME: circular dependency:
    _EXPIRATION_PRD = 4 * 32 # lnk_csma_ahsm.LnkHeymac._BCN_PRD


    def _process_bcn(self, frame):
        """Process a Heymac beacon and keeps relevant link data."""
        addr = frame.get_field(lnk_frame.HeymacFrame.FLD_SADDR)
        if addr not in self._ngbr_list:
            self._ngbr_list[addr] = {"BCN_CNT": 0}
        # TODO: create and use _NGBR_FLD_* names
        self._ngbr_list[addr]["BCN_FRAME"] = frame
        self._ngbr_list[addr]["BCN_CNT"] += 1

        # TODO: process nets[] to build list of known nets
