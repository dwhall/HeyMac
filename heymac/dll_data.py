#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.
"""


from . import mac_csma_cfg
from . import mac_tdma_cfg
from . import vdict


class DllData(object):
    """Data Link Layer (layer 2) data store.
    Uses dicts that keep timestamps to track dynamic data and its validity.
    """

    # If we don't hear a periodic item for N periods,
    # then we consider it expired/invalid
    N_EXPIRATION = 4


    def __init__(self,):
        cbcn_period = mac_csma_cfg.BEACON_PERIOD_SEC
        # NOTE: The following may need to become dynamic based on what's heard on the network.
        sbcn_period = (2 ** mac_tdma_cfg.FRAME_SPEC_SF_ORDER) / mac_tdma_cfg.TSLOTS_PER_SEC
        ebcn_period = (2 ** mac_tdma_cfg.FRAME_SPEC_EB_ORDER) * sbcn_period

        d = vdict.ValidatedDict()
        exp = DllData.N_EXPIRATION * sbcn_period
        d.set_default_expiration(exp)
        self.sbcns = d

        d = vdict.ValidatedDict()
        exp = DllData.N_EXPIRATION * ebcn_period
        d.set_default_expiration(exp)
        self.ebcns = d

        d = vdict.ValidatedDict()
        exp = DllData.N_EXPIRATION * cbcn_period
        d.set_default_expiration(exp)
        self.cbcns = d


    def process_heymac_frame(self, f):
        """Stores the given beacon and updates its timestamp.
        """
        if f.is_heymac_version_compatible():
            if f.is_sbcn():
                self.sbcns[f.saddr] = f.data
            elif f.is_ebcn():
                self.ebcns[f.saddr] = f.data
            elif f.is_cbcn():
                self.cbcns[f.saddr] = f.data


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
