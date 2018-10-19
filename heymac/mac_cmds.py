"""
Copyright 2017 Dean Hall.  See LICENSE file for details.

HeyMac Commands for MAC frame types:
# Standard Beacon
# Extended Beacon
# Text message
"""

import enum
import struct

import dpkt # pip install dpkt


# HeyMac Command IDs
class HeyMacCmdId(enum.IntEnum):
    """An enumeration of HeyMac MAC Command IDs.
    The Command ID occupies the first octet of a Command Packet.
    """
    INVALID = 0
    SBCN = 1
    EBCN = 2
    TXT = 3


class HeyMacCmd(dpkt.Packet):
    """A HeyMac MAC Command packet
    This class helps organize inheritance
    and can serve as a constructor for all command packets
    """
    pass
#    def __init__(self, cmd_id):
#        super().__init__()
# TODO: create instance of class using cmd_id or data


class HeyMacCmdInvalid(HeyMacCmd):
    """HeyMac Invalid command packet
    """
    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HeyMacCmdId.INVALID),
    )


class HeyMacCmdSbcn(HeyMacCmd):
    """HeyMac Standard Beacon command packet
    """

    FRAME_SPEC_BCN_EN_MASK = 0b10000000
    FRAME_SPEC_BCN_EN_SHIFT = 7
    FRAME_SPEC_EB_ORDER_MASK = 0b01110000
    FRAME_SPEC_EB_ORDER_SHIFT = 4
    FRAME_SPEC_SF_ORDER_MASK = 0b00001111
    FRAME_SPEC_SF_ORDER_SHIFT = 0

    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HeyMacCmdId.SBCN),
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
            return (self._frame_spec & HeyMacCmdSbcn.FRAME_SPEC_BCN_EN_MASK) >> HeyMacCmdSbcn.FRAME_SPEC_BCN_EN_SHIFT
        else:
            return None

    @property
    def sf_order(self,):
        """Gets the Sframe-order subfield from the frame spec
        """
        if self._frame_spec:
            return (self._frame_spec & HeyMacCmdSbcn.FRAME_SPEC_SF_ORDER_MASK) >> HeyMacCmdSbcn.FRAME_SPEC_SF_ORDER_SHIFT
        else:
            return None

    @property
    def eb_order(self,):
        """Gets the extended-beacon-order subfield from the frame spec
        """
        if self._frame_spec:
            return (self._frame_spec & HeyMacCmdSbcn.FRAME_SPEC_EB_ORDER_MASK) >> HeyMacCmdSbcn.FRAME_SPEC_EB_ORDER_SHIFT
        else:
            return None

    # Setters for underscore-prefixed fields
    @bcn_en.setter
    def bcn_en(self, val):
        """Sets the beacon-enabled subfield in the frame spec
        """
        if self._frame_spec:
            v = self._frame_spec & ~HeyMacCmdSbcn.FRAME_SPEC_BCN_EN_MASK
        else:
            v = 0
        self._frame_spec = v | (val << HeyMacCmdSbcn.FRAME_SPEC_BCN_EN_SHIFT)

    @sf_order.setter
    def sf_order(self, val):
        """Sets the Sframe-order subfield in the frame spec
        """
        assert val < 16, "SF Order exceeds limits"
        if self._frame_spec:
            v = self._frame_spec & ~HeyMacCmdSbcn.FRAME_SPEC_SF_ORDER_MASK
        else:
            v = 0
        self._frame_spec = v | (val << HeyMacCmdSbcn.FRAME_SPEC_SF_ORDER_SHIFT)

    @eb_order.setter
    def eb_order(self, val):
        """Sets the extended-beacon-order subfield in the frame spec
        """
        assert val < 8, "EB Order exceeds limits"
        if self._frame_spec:
            v = self._frame_spec & ~HeyMacCmdSbcn.FRAME_SPEC_EB_ORDER_MASK
        else:
            v = 0
        self._frame_spec = v | (val << HeyMacCmdSbcn.FRAME_SPEC_EB_ORDER_SHIFT)


    def pack_hdr(self):
        """Packs header attributes into a bytes object.
        This function is called when bytes() or len() is called
        on an instance of of this class.
        """
        b = bytearray(super().pack_hdr())

        # Pack the variable-length fields
        if not self.tx_slots:
            # Create a bytearray with 1 bit for every Tslot in an Sframe
            self.tx_slots = bytearray((2 ** self.sf_order) // 8)
        b.extend(self.tx_slots)
        if not self.ngbr_tx_slots:
            # Create a bytearray with 1 bit for every Tslot in an Sframe
            self.ngbr_tx_slots = bytearray((2 ** self.sf_order) // 8)
        b.extend(self.ngbr_tx_slots)

        return bytes(b)


    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when an instance of this class is created
        by passing a bytes object to the constructor
        """
        # Unpack the fixed-length fields
        super().unpack(buf)

        # The Frame Spec defines the size of tx_slots and ngbr_tx_slots
        sz = (2 ** self.sf_order) // 8
        if sz < 1:
            sz = 1

        # Unpack the variable-length fields
        hl = self.__hdr_len__
        self.tx_slots = buf[hl : hl + sz]
        self.ngbr_tx_slots = buf[hl + sz : hl + 2 * sz]
        assert len(self.ngbr_tx_slots) == sz, "len()=%d, sz=%d" % (len(self.ngbr_tx_slots), sz)

        # Do it this way so that an Sbcn's .data will be empty
        # but an Ebcn's .data will have extended data fields in there
        # (i.e. HeyMacCmdEbcn inherits from this class and re-uses this method)
        self.data = buf[hl + 2 * sz:]


class HeyMacCmdEbcn(HeyMacCmdSbcn):
    """HeyMac Extended Beacon command packet.
    Inherits from HeyMacCmdSbcn in order to re-use the property setters/getters
    because Ebcn shares many fields with Sbcn.
    """
    FRAME_SPEC_BCN_EN = 0b10000000
    FRAME_SPEC_BCN_EN_SHIFT = 7
    FRAME_SPEC_EB_ORDER_MASK = 0b01110000
    FRAME_SPEC_EB_ORDER_SHIFT = 4
    FRAME_SPEC_SF_ORDER_MASK = 0b00001111
    FRAME_SPEC_SF_ORDER_SHIFT = 0

    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HeyMacCmdId.EBCN),
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
        # Extended Beacon fields:
        ('station_id', '0s', b''),
        ('_nghbrs', '0s', b''),
        ('_ntwks', '0s', b''),
        ('geoloc', '0s', b''),
    )


    def pack_hdr(self):
        """Packs header attributes into a bytes object.
        This function is called when bytes() or len() is called
        on an instance of of this class.
        """
        # Pack the fields shared with Sbcn
        b = bytearray(super().pack_hdr())

        b.extend(self.station_id)
        # TODO: _nghbrs
        # TODO: _ntwks
        b.extend(self.geoloc)

        return bytes(b)


    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when an instance of this class is created
        by passing a bytes object to the constructor
        """
        # Unpack the fields shared with Sbcn
        super().unpack(buf)

        # Simple parsing for temporary data representation
        self.station_id, self.geoloc = self.data.split(b"$")

        # All data is used, so .data is emptied
        # so it doesn't show up in repr/prints
        self.data = b""


class HeyMacCmdTxt(HeyMacCmd):
    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HeyMacCmdId.TXT),
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

