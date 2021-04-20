"""
Copyright 2021 Dean Hall.  See LICENSE for details.

The Heymac Messages model.
"""

import bisect
import time

from ..lnk import HeymacCmdBcn, HeymacCmdTxt


class MsgsModel(object):
    """Abstract model of Heymac text messages.

    UI modules should use this class
    instead of interacting with HeymacCsmaHsm directly.
    """

    def __init__(self, lnk_hsm):
        self._lnk_hsm = lnk_hsm
        self._lnk_hsm.set_rx_clbk(self._rx_clbk)
        self._bcn_ident = {}
        self._callsigns = {}
        self._msg_data = []
        self._update_view = None


    def _rx_clbk(self, hm_frame):
        # TODO: blink status RX indicator
        if isinstance(hm_frame.cmd, HeymacCmdBcn):
            longaddr = hm_frame.get_field(hm_frame.FLD_SADDR)
            callsign = hm_frame.cmd.get_field(HeymacCmdBcn.FLD_CALLSIGN_SSID)
            self._callsigns[longaddr] = callsign

        elif isinstance(hm_frame.cmd, HeymacCmdTxt):
            rxtime = time.time()
            saddr = hm_frame.get_field(hm_frame.FLD_SADDR)
            msg = hm_frame.cmd.get_field(hm_frame.cmd.FLD_MSG)
            bisect.insort(self._msg_data, (rxtime, saddr, msg.decode()))

        if self._update_view:
            self._update_view()


    def get_callsigns(self):
        return self._callsigns


    def get_latest_msgs(self, n=0):
        return self._msg_data[-n:]


    def send_msg(self, msg):
        """Requests the link layer transmit the given message"""
        txt_cmd = HeymacCmdTxt(FLD_MSG=msg.encode())
        self._lnk_hsm.send_cmd(txt_cmd)

        txtime = time.time()
        saddr = self._lnk_hsm.get_lnk_addr()
        bisect.insort(self._msg_data, (txtime, saddr, msg))


    def set_update_clbk(self, clbk):
        self._update_view = clbk


