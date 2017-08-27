"""
Copyright 2017 Dean Hall.  See LICENSE file for details.

HeyMacBeacon - HeyMac protocol Beacon frame
"""


import struct

import HeyMacFrameMaker


class HeyMacBeacon(object):
    """HeyMac Beacon frame creation and parsing

    A HeyMac Beacon has a frame type of MAC and has the following structure::

        +----+----+----+----+----+----+----+----+
        |  Frame Command (1 octet)              |
        +----+----+----+----+----+----+----+----+
        |  Absolute Slot Number (4 octets)      |
        +----+----+----+----+----+----+----+----+
        |  SlotMap (4 octets)                   |
        +----+----+----+----+----+----+----+----+
    TODO:
        |  Neighbor data (variable octets)      |
        +----+----+----+----+----+----+----+----+
        |  Networks data (variable octets)      |
        +----+----+----+----+----+----+----+----+
    """

    MAC_CMD_BCN = 1

    def __init__(
        self,
        src_addr,       # source add
        asn,            # Absolute Slot Number
        slot_bitmap,    # 32b map of timeslots
        nghbrs,         # sequence of neighbor data
        nets,           # sequence of network data
        ):
        """Creates an instance of a beacon frame
        """
        self.f = HeyMacFrameMaker.HeyMacFrameMaker(
            fctl_type = 'mac',
            saddr = src_addr,
            )
        self.asn = asn
        self.slot_bitmap = slot_bitmap
        self.nghbrs = nghbrs
        self.nets = nets


    def update_asn(self, asn):
        self.asn = asn


    def __str__(self,):

        # TODO: Use MsgPack for all data when Nghbrs, Nets is added
        payld = struct.pack(
            "!BLL", 
            HeyMacBeacon.MAC_CMD_BCN,
            self.asn,
            self.slot_bitmap
            )

        # TODO: Append MsgPack data for Nghbrs, Nets

        self.f.add_field("payld", payld)

        return str(self.f)
