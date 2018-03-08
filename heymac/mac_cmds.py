"""
Copyright 2017 Dean Hall.  See LICENSE file for details.

HeyMac Commands for MAC frame type:
- HeyMac Beacon
"""


import dpkt


# HeyMac Command IDs
HEYMAC_CMD_BEACON = 1


class HeyMacCmdBeacon(dpkt.Packet):
    __hdr__ = (
        ('cmd', 'B', HEYMAC_CMD_BEACON),
        ('asn', 'I', 0),
        ('slotmap', 'I', 0), # REMOVE after old beacon is deprecated
#        ('dscpln_src', 'B', b"\x00"),     # 0:None, 1:RF, 2:GPS
#        ('dscpln_hops', 'B', b"\x00"),
#        ('caps', 'I', 0),   # capabilities
#        ('flags', 'I', 0),  # status flags
#        ('sframe_nchnls', 'B', b"\x01"),
#        ('sframe_hopLutId', 'B', b"\x00"),
#        ('sframe_nSlots', 'H', 0),
#        ('tx_slotmap', '4I', 0),    # 128 Tslots
#        ('ngbr_slotmap', '4I', 0),  # 128 Tslots
        # variable-length fields
# TODO:
#        ('_nghbrs', '0s', b''),
#        ('_ntwks', '0s', b''),
#        ('_geoloc', '0s', b'')
    )
