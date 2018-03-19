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
        ('dscpln', 'B', 0),     # 0x0X:None, 0x1X:RF, 0x2X:GPS (lower nibble is nhops to GPS)
        ('sframe_nTslots', 'H', 128),    # Number of Tslots per Sframe
        ('asn', 'I', 0),
        ('caps', 'I', 0),   # capabilities
        ('flags', 'I', 0),  # status flags
        ('tx_slotmap', '16B', (0,)*16),    # 128 Tslots
        ('ngbr_slotmap', '16B', (0,)*16),  # 128 Tslots
#        ('sframe_nchnls', 'B', b"\x01"), # Nmbr RF channels
#        ('sframe_hopLutId', 'B', b"\x00"), # Channel HOP lookup table ID
        # TODO: variable-length fields
#        ('_nghbrs', '0s', b''),
#        ('_ntwks', '0s', b''),
#        ('_geoloc', '0s', b'')
    )
