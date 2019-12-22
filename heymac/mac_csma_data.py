#!/usr/bin/env python3
"""
Copyright 2019 Dean Hall.  See LICENSE for details.

HeyMac CSMA MAC Layer Data

Data about this node:
- long addr
- caps (used in bcn)
x status (computed dynamically)

Neighbor list; for each neighbor:
- long addr
- time of last rx (to know when to drop ngbr)
- rx link Q (some func of recent rssi or snr)
- net id, net addr
"""


from . import mac_csma_cfg
from . import vdict


class MacData(object):
    """MAC Layer data store.
    Uses dicts that keep timestamps to track dynamic data and its validity.
    """

    # If we don't hear a periodic item for N periods,
    # then we consider it expired/invalid
    N_EXPIRATION = 4


    def __init__(self,):
        # d = vdict.ValidatedDict()
        # exp = MacData.N_EXPIRATION * mac_csma_cfg.BEACON_PERIOD_SEC
        # d.set_default_expiration(exp)
        # self.cbcns = d
        self.this_node = {}
        self.ngbr_list = []


    def process_beacon(self, frame_info):
        """Stores the given beacon and updates its timestamp.
        """
        f = frame_info.frame
        if not f.is_cbcn(): return
        self.cbcns[f.saddr] = f.data
        # TODO: store the link Q from the frame_info


    def get_cbcns(self,):
        """Returns dict of received CSMA beacons
        """
        return self.cbcns


    def get_ebcns(self,):
        """Returns dict of received beacons
        """
        return self.ebcns


    def get_bcn_slotmap(self, sf_order):
        """Returns a slotmap (bytearray) with a bit set
        for every valid 1-hop neighbor's beacon slot.
        The slotmap is sized according to the given sf_order.
        Neighbors are invalidated if we haven't heard from them
        in N_EXPIRATION beacon periods.
        """
        slotmap = bytearray((2 ** sf_order) // 8)
        for bcn in self.sbcns.values():
            if bcn.valid:
                bcnslot = bcn.value.asn % (2 ** sf_order)
                slotmap[ bcnslot // 8 ] |= (1 << (bcnslot % 8))
        return slotmap


    # TODO: def flush_bcn_ngbrs(self,):
    #    """Returns a list of neighbors who haven't beaconed lately.
    #    Removes the neighbors beacon data."""
