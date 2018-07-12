#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Data Link Layer (layer 2) Data store.
Tracks time-changing data.
"""


import mac_cfg
import mac_cmds
import vdict


# Some useful constants
TM_TSLOT_PERIOD = (1.0 / mac_cfg.TSLOTS_PER_SEC)
TM_SF_PERIOD = (2 ** mac_cfg.FRAME_SPEC_SF_ORDER) * TM_TSLOT_PERIOD
TM_EB_PERIOD = (2 ** mac_cfg.FRAME_SPEC_EB_ORDER) * TM_TSLOT_PERIOD
BCN_EXPIRATION = 4 * TM_SF_PERIOD


class DllData(object):

    def __init__(self,):
        self._d = {}
        self.init()


    def init(self,):
        self._d["bcn"] = vdict.ValidatedDict()


    def update_bcn(self, bcn, ngbr_addr):
        """Stores the given beacon and updates its timestamp.
        """
        assert isinstance(bcn, mac_cmds.HeyMacCmdSbcn)
        self._d["bcn"][ngbr_addr] = bcn
        self._d["bcn"].set_expiration(ngbr_addr, BCN_EXPIRATION)


    def get_bcn_slotmap(self,):
        """Returns a slotmap (bytearray) with a bit set
        for every valid 1-hop neighbor's beacon slot.
        Neighbors are invalid when they are silent for over 4 Sframes.
        """
        slotmap = bytearray((2 ** mac_cfg.FRAME_SPEC_SF_ORDER) // 8)
        for ngbr_addr in self._d["bcn"]:
            if self._d["bcn"][ngbr_addr].valid:
                bcnslot = self._d["bcn"][ngbr_addr].value.asn % (2 ** mac_cfg.FRAME_SPEC_SF_ORDER)
                slotmap[ bcnslot // 8 ] |= (1 << (bcnslot % 8))
        return slotmap

    # TODO: flush_bcn_ngbrs(self,):
    #    """Returns a list of neighbors who haven't beaconed lately.
    #    Removes the neighbors beacon data."""
