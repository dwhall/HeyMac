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
    CBCN = 4
    PROTO = 5


class HeyMacCmd(dpkt.Packet):
    """A HeyMac MAC Command packet
    This class helps organize inheritance
    and can serve as a constructor for all command packets
    """
    PREFIX = 0b10000000
    PREFIX_MASK = 0b11000000
    CMD_MASK = 0b00111111


class HeyMacCmdInvalid(HeyMacCmd):
    """HeyMac Invalid command packet
    """
    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HeyMacCmd.PREFIX | HeyMacCmdId.INVALID),
    )


class HeyMacCmdSbcn(HeyMacCmd):
    """HeyMac Standard Beacon command packet
    { 1, _frame_spec, dscpln, caps, status, asn, tx_slots, ngbr_tx_slots }
    """
    FRAME_SPEC_BCN_EN_MASK = 0b10000000
    FRAME_SPEC_BCN_EN_SHIFT = 7
    FRAME_SPEC_EB_ORDER_MASK = 0b01110000
    FRAME_SPEC_EB_ORDER_SHIFT = 4
    FRAME_SPEC_SF_ORDER_MASK = 0b00001111
    FRAME_SPEC_SF_ORDER_SHIFT = 0

    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HeyMacCmd.PREFIX | HeyMacCmdId.SBCN),
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

        # Ensure the given neighbor tx slotmap is the correct length or
        # create an empty neighbor tx slotmap of the correct length
        if self.tx_slots:
            assert len(self.tx_slots) == ((2 ** self.sf_order) // 8)
        else:
            self.tx_slots = bytearray((2 ** self.sf_order) // 8)
        b.extend(self.tx_slots)

        # Ensure the given neighbor tx slotmap is the correct length or
        # create an empty neighbor tx slotmap of the correct length
        if self.ngbr_tx_slots:
            assert len(self.ngbr_tx_slots) == ((2 ** self.sf_order) // 8)
        else:
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

        # The Frame Spec's SF Order value defines
        # the size of tx_slots and ngbr_tx_slots
        slotmap_sz = (2 ** self.sf_order) // 8
        if slotmap_sz < 1:
            slotmap_sz = 1

        # Unpack the slot maps
        hl = self.__hdr_len__
        self.tx_slots = buf[hl : hl + slotmap_sz]
        self.ngbr_tx_slots = buf[hl + slotmap_sz : hl + 2 * slotmap_sz]
        assert len(self.ngbr_tx_slots) == slotmap_sz, "len()=%d, slotmap_sz=%d" % (len(self.ngbr_tx_slots), slotmap_sz)

        # Do it this way so that an Sbcn's .data will be empty
        # but an Ebcn's .data will have extended data fields in there
        # (i.e. HeyMacCmdEbcn inherits from this class and re-uses this method)
        self.data = buf[hl + 2 * slotmap_sz:]


class HeyMacCmdEbcn(HeyMacCmdSbcn):
    """HeyMac Extended Beacon command packet.
    { 2, ...many fields... }
    Inherits from HeyMacCmdSbcn in order to re-use the property setters/getters
    because Ebcn shares many fields with Sbcn.
    """
    FRAME_SPEC_BCN_EN = 0b10000000
    FRAME_SPEC_BCN_EN_SHIFT = 7
    FRAME_SPEC_EB_ORDER_MASK = 0b01110000
    FRAME_SPEC_EB_ORDER_SHIFT = 4
    FRAME_SPEC_SF_ORDER_MASK = 0b00001111
    FRAME_SPEC_SF_ORDER_SHIFT = 0

    NGBR_FMT = "8sBB"
    NTWK_FMT = "!H8sH"

    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HeyMacCmd.PREFIX | HeyMacCmdId.EBCN),
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
        ('_ngbrs', '0s', b''),
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

        # Pack the Station ID and ensure it has a null terminator
        b.extend(self.station_id)
        if self.station_id[-1] != b'\x00':
            b.append(0)

        self.pack_ngbrs(b)
        self.pack_ntwks(b)
        b.extend(self.geoloc)

        return bytes(b)


    def pack_ngbrs(self, b):
        """Packs neighbor data and appends it
        to the given bytearray
        """
        if hasattr(self, "ngbrs"):
            b.append(len(self.ngbrs))  # Count of neighbors
            for n in self.ngbrs:
                b.extend(struct.pack(HeyMacCmdEbcn.NGBR_FMT, n[0], n[1], n[2]))
        else:
            b.append(0) # Count of neighbors


    def pack_ntwks(self, b):
        """Packs network data and appends it
        to the given bytearray
        """
        if hasattr(self, "ntwks"):
            b.append(len(self.ntwks))  # Count of networks
            for n in self.ntwks:
                b.extend(struct.pack(HeyMacCmdEbcn.NTWK_FMT, n[0], n[1], n[2]))
        else:
            b.append(0) # Count of networks


    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when an instance of this class is created
        by passing a bytes object to the constructor
        """
        # Unpack the fields shared with Sbcn
        # (expects self.data to be set with leftover data)
        super().unpack(buf)

        # Station ID is a null-terminated, variable-length UTF-8 string
        first_null = self.data.find(b"\x00")
        assert first_null > 0
        # Increment first_null so that station_id includes
        # the null term and self.data does not
        first_null += 1

        self.station_id = self.data[:first_null]
        self.data = self.data[first_null:]

        self.ngbrs = self.unpack_ngbrs()
        self.ntwks = self.unpack_ntwks()

        # TODO: unpack geoloc properly and ensure no leftover data
        self.geoloc = self.data
        self.data = []


    def unpack_ngbrs(self,):
        """Returns the unpacked Neighbors data.
        Neighbors is a sequence of (address, SNR, RSSI) tuples
        the first byte is the number of tuples in the sequence
        """
        ngbrs_cnt = self.data[0]
        offset = 1
        ngbrs = []
        for n in range(ngbrs_cnt):
            ngbrs.append(struct.unpack_from(HeyMacCmdEbcn.NGBR_FMT, self.data, offset))
            offset += struct.calcsize(HeyMacCmdEbcn.NGBR_FMT)
        self.data = self.data[offset:]
        return ngbrs


    def unpack_ntwks(self,):
        """Returns the unpacked networks data.
        Networks is a sequence of (NetId, RootAddr, HONR) tuples
        the first byte is the number of tuples in the sequence
        """
        ntwks_cnt = self.data[0]
        offset = 1
        ntwks = []
        for n in range(ntwks_cnt):
            ntwks.append(struct.unpack_from(HeyMacCmdEbcn.NTWK_FMT, self.data, offset))
            offset += struct.calcsize(HeyMacCmdEbcn.NTWK_FMT)
        self.data = self.data[offset:]
        return ntwks


class HeyMacCmdTxt(HeyMacCmd):
    """HeyMac Text message command packet
    { 3, msg }
    """
    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HeyMacCmd.PREFIX | HeyMacCmdId.TXT),
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


class HeyMacCmdCbcn(HeyMacCmd):
    """HeyMac CSMA Beacon command packet
    { 4, caps, status, nets[], ngbrs[] } # NOTE: form not finalized
    """
    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HeyMacCmd.PREFIX | HeyMacCmdId.CBCN),
        ('caps', 'H', 0),
        ('status', 'H', 0),
        # variable-length fields:
        ('nets', '0s', b''),    # N, N * [netid, shrt_addr]
        ('ngbrs', '0s', b''),   # N, N * long_addr
    )


class HeyMacCmdProtocol(HeyMacCmd):
    """HeyMac Protocol command packet
    { 5, pid, mid }
    """
    PID_INVAL = 0
    PID_NET_JOIN = 1
    PID_NET_LEAVE = 2

    MID_NAK = 0
    MID_NET_JOIN_RQST = 1
    MID_NET_JOIN_ACCPT = 2
    MID_NET_JOIN_NTFY = 3
    MID_NET_JOIN_RJCT = 4

    __byte_order__ = '!' # Network order
    __hdr__ = (
        ('cmd', 'B', HeyMacCmd.PREFIX | HeyMacCmdId.PROTO),
        ('pid', 'B', 0), # Protocol ID
        ('mid', 'B', 0), # Message ID
    )


# EVERYTHING BELOW THIS MUST BE AT THE BOTTOM OF THE FILE

# The order of this LUT must match HeyMacCmdId
CMD_CLASS_LUT = (
    HeyMacCmdInvalid,   # INVALID = 0
    HeyMacCmdSbcn,
    HeyMacCmdEbcn,
    HeyMacCmdTxt,
    HeyMacCmdCbcn,
    HeyMacCmdProtocol,  # PROTO = 5
)


def HeyMacCmdInstance(mac_payld):
    """Returns an instance of one of the HeyMacCmd classes
    based on the command id (within the first byte of mac_payld).
    """
    cmd_id = mac_payld[0] & HeyMacCmd.CMD_MASK
    return CMD_CLASS_LUT[cmd_id](mac_payld)
