"""
Copyright 2017 Dean Hall.  See LICENSE file for details.

HeyMac Commands for MAC frame type:
- HeyMac Small Beacon
"""

import struct

import dpkt # pip install dpkt


# HeyMac Command IDs
HEYMAC_CMD_SM_BCN = 1
HEYMAC_CMD_EXT_BCN = 2
HEYMAC_CMD_TXT = 3


class CmdPktSmallBcn(dpkt.Packet):
    """HeyMac Small Beacon command packet
    """

    FRAME_SPEC_BCN_EN_MASK = 0b10000000
    FRAME_SPEC_BCN_EN_SHIFT = 7
    FRAME_SPEC_SF_ORDER_MASK = 0b01110000
    FRAME_SPEC_SF_ORDER_SHIFT = 4
    FRAME_SPEC_EB_ORDER_MASK = 0b00001111
    FRAME_SPEC_EB_ORDER_SHIFT = 0

    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HEYMAC_CMD_SM_BCN),
        # The underscore prefix means do not access that field directly.
        # Access properties: .bcn_en, .sf_order and .eb_order, instead.
        ('_frame_spec', 'B', 0),
        ('dscpln', 'B', 0), # 0x0X:None, 0x1X:RF, 0x2X:GPS (lower nibble is nhops to GPS)
        ('caps', 'B', 0),
        ('status', 'B', 0),
        ('asn', 'I', 0),
        # variable-length fields:
        ('tx_slots', '0s', b''),
        ('ngbr_tx_slots', '0s', b''),
    )

    # Getters for underscore-prefixed fields
    @property
    def bcn_en(self,):
        """Gets the beacon-enabled subfield from the frame spec
        """
        if self._frame_spec:
            return (self._frame_spec[0] & CmdPktSmallBcn.FRAME_SPEC_BCN_EN_MASK) >> CmdPktSmallBcn.FRAME_SPEC_BCN_EN_SHIFT
        else:
            return None

    @property
    def sf_order(self,):
        """Gets the Sframe-order subfield from the frame spec
        """
        if self._frame_spec:
            return (self._frame_spec[0] & CmdPktSmallBcn.FRAME_SPEC_SF_ORDER_MASK) >> CmdPktSmallBcn.FRAME_SPEC_SF_ORDER_SHIFT
        else:
            return None

    @property
    def eb_order(self,):
        """Gets the extended-beacon-order subfield from the frame spec
        """
        if self._frame_spec:
            return (self._frame_spec[0] & CmdPktSmallBcn.FRAME_SPEC_EB_ORDER_MASK) >> CmdPktSmallBcn.FRAME_SPEC_EB_ORDER_SHIFT
        else:
            return None

    # Setters for underscore-prefixed fields
    @bcn_en.setter
    def bcn_en(self, val):
        """Sets the beacon-enabled subfield in the frame spec
        """
        if self._frame_spec:
            v = self._frame_spec & ~CmdPktSmallBcn.FRAME_SPEC_BCN_EN_MASK
        else:
            v = 0
        self._frame_spec = v | (val << CmdPktSmallBcn.FRAME_SPEC_BCN_EN_SHIFT)

    @sf_order.setter
    def sf_order(self, val):
        """Sets the Sframe-order subfield in the frame spec
        """
        if self._frame_spec:
            v = self._frame_spec & ~CmdPktSmallBcn.FRAME_SPEC_SF_ORDER_MASK
        else:
            v = 0
        self._frame_spec = v | (val << CmdPktSmallBcn.FRAME_SPEC_SF_ORDER_SHIFT)

    @eb_order.setter
    def eb_order(self, val):
        """Sets the extended-beacon-order subfield in the frame spec
        """
        if self._frame_spec:
            v = self._frame_spec & ~CmdPktSmallBcn.FRAME_SPEC_EB_ORDER_MASK
        else:
            v = 0
        self._frame_spec = v | (val << CmdPktSmallBcn.FRAME_SPEC_EB_ORDER_SHIFT)


    def pack_hdr(self):
        """Packs header attributes into a bytes object.
        This function is called when bytes() or len() is called
        on an instance of of this class.
        """
        b = bytearray()

        # Pack the fixed-length fields
        b.append(self.cmd)
        b.append(self.frame_spec)
        b.append(self.dscpln)
        b.append(self.caps)
        b.append(self.status)
        b.extend(struct.pack(CmdPktSmallBcn.__byte_order__ + "i", self.asn))
        # Pack the variable-length fields
        b.extend(self.tx_slots)
        b.extend(self.ngbr_tx_slots)

        return bytes(b)


    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when an instance of this class is created
        by passing a bytes object to the constructor
        """
        # Unpack the fixed-length fields
        super(CmdPktSmallBcn, self).unpack(buf)

        # The Frame Spec defines the size of tx_slots and ngbr_tx_slots
        frOrder = (CmdPktSmallBcn.FRAME_SPEC_SF_ORDER_MASK & self.frame_spec) \
                >> CmdPktSmallBcn.FRAME_SPEC_SF_ORDER_SHIFT
        sz = (2 ** frOrder) // 8
        if sz < 1: sz = 1

        # Unpack the variable-length fields
        hl = self.__hdr_len__
        self.tx_slots = buf[hl : hl + sz]
        self.ngbr_tx_slots = buf[hl + sz:]
        assert len(self.ngbr_tx_slots) == sz

        self.data = bytes()


class CmdPktExtBcn(dpkt.Packet):
    """HeyMac Extended Beacon command packet
    """
    FRAME_SPEC_BCN_EN = 0b10000000
    FRAME_SPEC_BCN_EN_SHIFT = 7
    FRAME_SPEC_SF_ORDER_MASK = 0b01110000
    FRAME_SPEC_SF_ORDER_SHIFT = 4
    FRAME_SPEC_EB_ORDER_MASK = 0b00001111
    FRAME_SPEC_EB_ORDER_SHIFT = 0

    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HEYMAC_CMD_EXT_BCN),
        # Small Beacon fields:
        ('frame_spec', 'B', 0),
        ('dscpln', 'B', 0), # 0x0X:None, 0x1X:RF, 0x2X:GPS (lower nibble is nhops to GPS)
        ('caps', 'B', 0),
        ('status', 'B', 0),
        ('asn', 'I', 0),
        # variable-length fields:
        ('tx_slots', '0s', b''),
        ('ngbr_tx_slots', '0s', b''),
        # Extended Beacon fields:
        ('station_id', '0s', b''),
        ('_nghbrs', '0s', b''),
        ('_ntwks', '0s', b''),
        ('geoloc', '0s', b''),
    )


class CmdPktTxt(dpkt.Packet):
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
