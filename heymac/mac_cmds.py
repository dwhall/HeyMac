"""
Copyright 2017 Dean Hall.  See LICENSE file for details.

HeyMac Commands for MAC frame type:
- HeyMac Beacon
"""


import dpkt


# HeyMac Command IDs
HEYMAC_CMD_BEACON = 1
HEYMAC_CMD_TXT = 2


class HeyMacCmdBeacon(dpkt.Packet):
    __byte_order__ = '!' # Network order
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
        ('callsign', '0s', b''),
#        ('_nghbrs', '0s', b''),
#        ('_ntwks', '0s', b''),
        ('geoloc', '0s', b''),
    )


    def __len__(self):
        return self.__hdr_len__ + len(self.callsign) + len(self.geoloc)


    def __bytes__(self):
        return self.pack_hdr() + bytes(self.callsign) + bytes(self.geoloc)


    def unpack(self, buf):
        # Unpack the fixed-length fields
        dpkt.Packet.unpack(self, buf)

        # Unpack the variable-length fields
        start_of_geoloc = buf.rfind(b"$")
        self.callsign = buf[self.__hdr_len__:start_of_geoloc]
        self.geoloc = buf[start_of_geoloc:]
        self.data = bytes()


class HeyMacCmdTxt(dpkt.Packet):
    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HEYMAC_CMD_TXT),
        ('msg', '0s', b''),
    )

    def __len__(self):
        return self.__hdr_len__ + len(self.msg)


    def __bytes__(self):
        return self.pack_hdr() + bytes(self.msg)


    def unpack(self, buf):
        # Unpack the fixed-length fields
        dpkt.Packet.unpack(self, buf)

        # Unpack the variable-length field
        self.msg = buf[self.__hdr_len__:]
        self.data = bytes()


def test():
    bcn = HeyMacCmdBeacon(
        dscpln=1,
        sframe_nTslots=2,
        asn=3,
        caps=4,
        flags=5,
        tx_slotmap=tuple(range(16)),
        ngbr_slotmap=tuple(range(0x80,0x80+16)),)
    bcn.callsign=b"KC4KSU"
    bcn.geoloc=b"$GPRMC,225446,A,4916.45,N,12311.12,W,000.5,054.7,191194,020.3,E*68"
    print(repr(bcn))
    print(repr(HeyMacCmdBeacon(bytes(bcn))))

    txt = HeyMacCmdTxt(msg=b"Hell, oh! whirled")
    print(repr(txt))
    print(repr(HeyMacCmdTxt(bytes(txt))))


if __name__ == '__main__':
    test()
