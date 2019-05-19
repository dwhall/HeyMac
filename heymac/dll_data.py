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
        self._bcn_expiration = bcn_expiration
        self._ebcn_expiration = ebcn_expiration

        d = vdict.ValidatedDict()
        d.set_default_expiration(bcn_expiration)
        self.bcns = d

        d = vdict.ValidatedDict()
        d.set_default_expiration(ebcn_expiration)
        self.ebcns = d


    def process_heymac_frame(self, f):
        """Stores the given beacon and updates its timestamp.
        """
        if f.is_heymac_version_compatible():
            if f.is_sbcn():
                self.bcns[f.saddr] = f.data
            elif f.is_ebcn():
                self.ebcns[f.saddr] = f.data


    def get_ebcns(self,):
        """Returns dict of received beacons
        """
        return self.ebcns


    def get_bcn_slotmap(self, sf_order):
        """Returns a slotmap (bytearray) with a bit set
        for every valid 1-hop neighbor's beacon slot.
        The slotmap is sized according to the given sf_order.
        Neighbors are invalid when they are silent for over 4 Sframes.
        """
        slotmap = bytearray((2 ** sf_order) // 8)
        for bcn in self.bcns.values():
            if bcn.valid:
                bcnslot = bcn.value.asn % (2 ** sf_order)
                slotmap[ bcnslot // 8 ] |= (1 << (bcnslot % 8))
        return slotmap

    # TODO: flush_bcn_ngbrs(self,):
    #    """Returns a list of neighbors who haven't beaconed lately.
    #    Removes the neighbors beacon data."""
