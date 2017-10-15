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
        ('slotmap', 'I', 0),
        # variable-length fields
# TODO:
#        ('_nghbrs', '0s', b''),
#        ('_ntwks', '0s', b''),
    )
