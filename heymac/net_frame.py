#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.

APv6 (network layer) frame structure definition

This file uses the excellent dpkt third-party module
to define the structure of the APv6 network layer frames.
An APv6 frame can be created by creating an instance of APv6Frame()
with any field_name=value as an argument to the constructor.
And an APv6 frame may be accessed via instance.field_name.
"""


import struct

import dpkt # pip install dpkt

# from .trn_udp import APv6Udp # moved to unpack() to fix circular dependancy


class APv6Frame(dpkt.Packet):
    """APv6 frame definition
    """
    IPHC_PREFIX_MASK = 0b11100000
    IPHC_NHC_MASK = 0b00010000
    IPHC_HLIM_MASK = 0b00001100
    IPHC_SAM_MASK = 0b00000010
    IPHC_DAM_MASK = 0b00000001

    IPHC_PREFIX_SHIFT = 5
    IPHC_NHC_SHIFT = 4
    IPHC_HLIM_SHIFT = 2
    IPHC_SAM_SHIFT = 1
    IPHC_DAM_SHIFT = 0

    IPHC_PREFIX = 0b110

    IPHC_HLIM_INLINE = 0b00 # HopLimit (1 Byte) follows IPHC
    IPHC_HLIM_1 = 0b01
    IPHC_HLIM_64 = 0b10
    IPHC_HLIM_255 = 0b11

    IPHC_ADDR_MODE_128 = 0 # full 128-bit address is in-lin
    IPHC_ADDR_MODE_0 = 1 # address is elided

    APV6_PREFIX = IPHC_PREFIX << IPHC_PREFIX_SHIFT

    DEFAULT_NHC = 0b1 # next-header is compressed
    DEFAULT_HLIM = IPHC_HLIM_1 # 1 hop
    DEFAULT_SAM = IPHC_ADDR_MODE_0 # address compressed/elided
    DEFAULT_DAM = IPHC_ADDR_MODE_0 # address compressed/elided


    __byte_order__ = '!' # Network order
    __hdr__ = (
        # The underscore prefix means do not access that field directly.
        # Access properties .iphc, .iphc_nhc, etc. instead.
        ('_iphc', 'B', APV6_PREFIX),
        # Fields with '0s' are optional or variable-length
        ('hops', '0s', b''),
        ('src', '0s', b''),
        ('dst', '0s', b''),
    )

    # Functions to help determine which fields are present
    def _has_hops_field(self,):
        return ((self._iphc & APv6Frame.IPHC_HLIM_MASK ) >> APv6Frame.IPHC_HLIM_SHIFT) == APv6Frame.IPHC_HLIM_INLINE
    def _has_src_field(self,):
        return ((self._iphc & APv6Frame.IPHC_SAM_MASK ) >> APv6Frame.IPHC_SAM_SHIFT) == APv6Frame.IPHC_ADDR_MODE_128
    def _has_dst_field(self,):
        return ((self._iphc & APv6Frame.IPHC_DAM_MASK ) >> APv6Frame.IPHC_DAM_SHIFT) == APv6Frame.IPHC_ADDR_MODE_128

    # Getters for the _iphc subfields
    @property
    def iphc(self,):
        """Gets the full value (all bits) from the IPHC field.
        """
        return self._iphc

    @property
    def iphc_prefix(self,):
        """Returns the APv6 prefix.
        The value should be 3b110 according to APv6 1.0 spec.
        This value is different than RFC6282 which specifies 3b011.
        """
        return (self._iphc & APv6Frame.IPHC_PREFIX_MASK) >> APv6Frame.IPHC_PREFIX_SHIFT

    @property
    def iphc_nhc(self,):
        """Returns bit pattern to indicate Next Header Compressed.
        0: Next Header is carried in-line
        1: Next Header is encoded via LOWPAN_NHC
        """
        return (self._iphc & APv6Frame.IPHC_NHC_MASK) >> APv6Frame.IPHC_NHC_SHIFT

    @property
    def iphc_hlim(self,):
        """Returns the bit pattern to indicate the Hop Limit
        0: Hop Limit is carried in-line
        1: Hop Limit is 1
        2: Hop Limit is 64
        3: Hop Limit is 255
        """
        return (self._iphc & APv6Frame.IPHC_HLIM_MASK) >> APv6Frame.IPHC_HLIM_SHIFT

    @property
    def iphc_sam(self,):
        """Returns bit pattern to indicate Source Address mode.
        0: Src Addr is carried in-line
        1: Src Addr is elided; computed from MAC layer
        """
        return (self._iphc & APv6Frame.IPHC_SAM_MASK) >> APv6Frame.IPHC_SAM_SHIFT

    @property
    def iphc_dam(self,):
        """Returns bit pattern to indicate Destination Address mode.
        0: Dest Addr is carried in-line
        1: Dest Addr is elided; computed from MAC layer
        """
        return (self._iphc & APv6Frame.IPHC_DAM_MASK) >> APv6Frame.IPHC_DAM_SHIFT


    # Setters for the _iphc subfields
    @iphc.setter
    def iphc(self, val):
        """Sets the whole value of the IPHC field.
        """
        assert ((val & APv6Frame.IPHC_PREFIX_MASK) >> APv6Frame.IPHC_PREFIX_SHIFT) == IPHC_PREFIX, "Invalid APv6 prefix"
        assert 0 <= val < 256
        self._iphc = val

    @iphc_nhc.setter
    def iphc_nhc(self, val):
        """Sets the Next Header Compressed bit in the IPHC field to the given value
        """
        assert 0 <= val <= 1
        assert val == APv6Frame.DEFAULT_NHC, "only compressed headers are supported at this time"

        self._iphc = (self._iphc & ~APv6Frame.IPHC_NHC_MASK) | ((val & 1) << APv6Frame.IPHC_NHC_SHIFT)

    @iphc_hlim.setter
    def iphc_hlim(self, val):
        """Sets the Next Header bit in the IPHC field to the given value
        """
        assert 0 <= val < 4
        self._iphc = (self._iphc & ~APv6Frame.IPHC_HLIM_MASK) | ((val & 0b11) << APv6Frame.IPHC_HLIM_SHIFT)

    @iphc_sam.setter
    def iphc_sam(self, val):
        """Sets the Source Address Mode bit in the IPHC field to the given value
        """
        assert 0 <= val < 2
        self._iphc = (self._iphc & ~APv6Frame.IPHC_SAM_MASK) | ((val & 1) << APv6Frame.IPHC_SAM_SHIFT)

    @iphc_dam.setter
    def iphc_dam(self, val):
        """Sets the Destination Address Mode bit in the IPHC field to the given value
        """
        assert 0 <= val < 2
        self._iphc = (self._iphc & ~APv6Frame.IPHC_DAM_MASK) | ((val & 1) << APv6Frame.IPHC_DAM_SHIFT)


    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when an instance of this class is created
        by passing a bytes object to the constructor
        """
        super().unpack(buf)  # unpacks _iphc

        # Hops is in the byte following the IPHC field
        if self._has_hops_field():
            if len(self.data) < 1:
                raise dpkt.NeedData("for hops")
            self.hops = self.data[0]
            self.data = self.data[1:]

        # Hops is encoded in the IPHC HLIM field
        else:
            if self.iphc_hlim == 0b01:
                self.hops = 1
            if self.iphc_hlim == 0b10:
                self.hops = 64
            if self.iphc_hlim == 0b11:
                self.hops = 255

        if self._has_src_field():
            if len(self.data) < 16:
                raise dpkt.NeedData("for src")
            self.src = self.data[0:16]
            self.data = self.data[16:]

        if self._has_dst_field():
            if len(self.data) < 16:
                raise dpkt.NeedData("for dst")
            self.dst = self.data[0:16]
            self.data = self.data[16:]

        # Unpack the payload for known frame types
        if (self.iphc_prefix == APv6Frame.IPHC_PREFIX and len(self.data) > 1):
            # TODO: check for uncompressed UDP, too
            # If the compressed next-header indicates compressed-UDP
            if self.iphc_nhc == 1 and self.data[0] & 0b11111000 == 0b11110000:
                from .trn_udp import APv6Udp
                self.data = APv6Udp(self.data)


    def pack_hdr(self):
        """Packs header attributes into a bytes object.
        This function is called when bytes() or len() is called
        on an instance of Apv6Frame.
        """
        d = bytearray()

        # Skip IPHC field for now, insert it at the end of this function

        # Only compressed next-headers are supported at this time
        self.iphc_nhc = APv6Frame.DEFAULT_NHC

        if self.hops:
            if type(self.hops) is bytes:
                v = self.hops[0]
            else:
                v = self.hops
                self.hops = struct.pack("B", v)
            if v == 1:
                self.iphc_hlim = 0b01
            elif v == 64:
                self.iphc_hlim = 0b10
            elif v == 255:
                self.iphc_hlim = 0b11
            else:
                self.iphc_hlim = 0b00
                d.append(v)
        else:
            if not self.iphc_hlim:
                self.iphc_hlim = APv6Frame.DEFAULT_HLIM

        if self.src:
            if len(self.src) == 16:
                self.iphc_sam = 0
                d.extend(self.src)
        else:
            self.iphc_sam = APv6Frame.DEFAULT_SAM

        if self.dst:
            if len(self.dst) == 16:
                self.iphc_dam = 0
                d.extend(self.dst)
        else:
            self.iphc_dam = APv6Frame.DEFAULT_DAM

        return super().pack_hdr() + bytes(d)
