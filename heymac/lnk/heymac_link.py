"""Copyright 2020 Dean Hall.  See LICENSE for details.
"""


import farc

from .heymac_frame import HeymacFrame
from .heymac_cmd import HeymacCmdBcn


class HeymacLink(object):
    """Heymac link layer data.

    _ngbr_data is a dict that holds data for each neighbor.
    The neighbor's link address is the key.  The value is a dict with items:

    ==================  =======================================================
    Key                 Value
    ==================  =======================================================
    "BCN_CNT"           the number of beacons received since link established
    "BCN_FRAME"         instance of HeymacCmdBcn
    "LATEST_RX_TM"      time of latest RX of any valid HeymacFrame from ngbr
    "LATEST_RX_RSSI"    RSSI of latest RX of any valid HeymacFrame from ngbr
    "LATEST_RX_SNR"     SNR of latest RX of any valid HeymacFrame from ngbr
    ==================  =======================================================
    """
    def __init__(self, lnk_addr):
        self._lnk_addr = lnk_addr
        self._ngbrs = {}


    def get_ngbrs_lnk_addrs(self):
        """Returns a list of neighbors' link addresses."""
        return self._ngbrs.keys()


    def ngbr_hears_me(self):
        """Does a neighbor node hear this node.

        Returns True if at least one neighbor has this node
        in its neighbor data.  This proves two-way transmission
        has taken place.
        """
        found_me = False
        for ngbr_data in self._ngbrs.values():
            if ngbr_data["BCN_CNT"] > 0:
                # FIXME: bcn frame no longer carries ngbr list
                # frame = ngbr_data["BCN_FRAME"]
                # bcn = frame.cmd
                # assert type(bcn) is HeymacCmdBcn
                # ngbrs_ngbrs = bcn.get_field(HeymacCmd.FLD_NGBRS)
                # if self._lnk_addr in ngbrs_ngbrs:
                #    found_me = True
                pass
        return found_me


    def process_frame(self, frame):
        """Update link data with info from the given frame."""
        assert type(frame) is HeymacFrame

        # Init data for a new neighbor
        lnk_addr = frame.get_sender()
        if lnk_addr not in self._ngbrs:
            self._ngbrs[lnk_addr] = {"BCN_CNT": 0}

        # Update rx meta data
        d = self._ngbrs[lnk_addr]
        d["LATEST_RX_TM"] = frame.rx_meta[0]
        d["LATEST_RX_RSSI"] = frame.rx_meta[1]
        d["LATEST_RX_SNR"] = frame.rx_meta[2]

        # Process a beacon
        if frame.cmd and type(frame.cmd) is HeymacCmdBcn:
            self._process_bcn(frame)


    def update(self):
        """Performs periodic update of the link data."""
        now = farc.Framework._event_loop.time()
        # Collect and prune expired neighbors
        expired_ngbrs = []
        for ngbr_addr, ngbr_data in self._ngbrs.items():
            frame = ngbr_data["BCN_FRAME"]
            rx_time = frame.rx_meta[0]
            if now > rx_time + self._EXPIRATION_PRD:
                expired_ngbrs.append(ngbr_addr)
        for ngbr_addr in expired_ngbrs:
            del self._ngbrs[ngbr_addr]


# Private


    # If we don't hear a neighbor (or periodic item)
    # for this many seconds then consider it expired/invalid
    # FIXME: circular dependency:
    _EXPIRATION_PRD = 4 * 32    # heymac_hsm.Heymac._BCN_PRD


    def _process_bcn(self, frame):
        """Process a Heymac beacon and keeps relevant link data."""
        lnk_addr = frame.get_sender()
        d = self._ngbrs[lnk_addr]
        d["BCN_FRAME"] = frame
        d["BCN_CNT"] += 1
