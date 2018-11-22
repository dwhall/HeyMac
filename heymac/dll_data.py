#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.

Data Link Layer (layer 2) Data store.
Tracks time-changing data.
"""


from . import mac_cmds
from . import vdict


class DllData(object):

    def __init__(self, bcn_expiration, ebcn_expiration):
        self._d = {}
        self._bcn_expiration = bcn_expiration
        self._ebcn_expiration = ebcn_expiration

        d = vdict.ValidatedDict()
        d.set_default_expiration(bcn_expiration)
        self._d["bcn"] = d

        d = vdict.ValidatedDict()
        d.set_default_expiration(ebcn_expiration)
        self._d["ebcn"] = d


    def update_bcn(self, bcn, ngbr_addr):
        """Stores the given beacon and updates its timestamp.
        """
        if type(bcn) is mac_cmds.HeyMacCmdSbcn:
            self._d["bcn"][ngbr_addr] = bcn
        elif type(bcn) is mac_cmds.HeyMacCmdEbcn:
            self._d["ebcn"][ngbr_addr] = bcn


    def get_ebcns(self,):
        """Returns dict of received beacons
        """
        return self._d["ebcn"]


    def get_bcn_slotmap(self, sf_order):
        """Returns a slotmap (bytearray) with a bit set
        for every valid 1-hop neighbor's beacon slot.
        The slotmap is sized according to the given sf_order.
        Neighbors are invalid when they are silent for over 4 Sframes.
        """
        slotmap = bytearray((2 ** sf_order) // 8)
        for bcn in self._d["bcn"].values():
            if bcn.valid:
                bcnslot = bcn.value.asn % (2 ** sf_order)
                slotmap[ bcnslot // 8 ] |= (1 << (bcnslot % 8))
        return slotmap

    # TODO: flush_bcn_ngbrs(self,):
    #    """Returns a list of neighbors who haven't beaconed lately.
    #    Removes the neighbors beacon data."""
