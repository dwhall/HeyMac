"""
Copyright 2017 Dean Hall.  See LICENSE file for details.

HeyMac Commands for MAC frame type:
- HeyMac Beacon
"""


import dpkt

from HeyMac import *


# HeyMac Command IDs
HEYMAC_CMD_BCN = 1


class HeyMacBeacon(dpkt.Packet):
    """HeyMac Beacon

        +----+----+----+----+----+----+----+----+
        |  Frame Command (1 octet)              |
        +----+----+----+----+----+----+----+----+
        |  Absolute Slot Number (4 octets)      |
        +----+----+----+----+----+----+----+----+
        |  SlotBitmap (4 octets)                |
        +----+----+----+----+----+----+----+----+
    TODO:
        |  Neighbor data (variable octets)      |
        +----+----+----+----+----+----+----+----+
        |  Networks data (variable octets)      |
        +----+----+----+----+----+----+----+----+
    """

    __hdr__ = (
        ('cmd', 'B', HEYMAC_CMD_BCN),
        ('asn', 'I', 0),
        ('slotmap', 'I', 0),
        # variable-length fields
#        ('_nghbrs', '0s', b''),
#        ('_ntwks', '0s', b''),
    )
