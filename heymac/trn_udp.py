#!/usr/bin/env python3
"""
Copyright 2018 Dean Hall.  See LICENSE for details.

UDP frame structure definition

This file uses the excellent dpkt third-party module
to define the structure of the compressed UDP frame.
The UDP frame is compressed according to RFC6282.

APv6Frame (outside this module) provides the IPHC, hops and addressing
and APv6Udp provides the header type, checksum and ports.
"""


import struct

import dpkt # pip install dpkt


class APv6Udp(dpkt.Packet):
    """APv6 UDP packet definition
    Derived from RFC6282
    """
    HDR_TYPE = 0b11110

    HDR_TYPE_MASK = 0b11111000
    HDR_CO_MASK = 0b00000100
    HDR_PORTS_MASK = 0b00000011

    HDR_TYPE_SHIFT = 3
    HDR_CO_SHIFT = 2
    HDR_PORTS_SHIFT = 0

    HDR_PORTS_SRC_INLN_DST_INLN = 0b00
    HDR_PORTS_SRC_INLN_DST_F0XX = 0b01
    HDR_PORTS_SRC_F0XX_DST_INLN = 0b10
    HDR_PORTS_SRC_F0BX_DST_F0BX = 0b11

    DEFAULT_CHKSUM = b""


    __hdr__ = (
        # The underscore prefix means do not access that field directly.
        # Access properties .hdr_type, .hdr_co and .hdr_ports, instead.
        ('_hdr', 'B', HDR_TYPE << HDR_TYPE_SHIFT), # RFC6282 4.3.3.  UDP LOWPAN_NHC Format
        # Fields with '0s' are optional or variable-length
        ('chksum', '0s', b''),
        ('src_port', '0s', b''),
        ('dst_port', '0s', b''),
    )

    # Getters of _hdr
    @property
    def hdr_type(self,):
        """Returns UDP Header's Type field.
        RFC6282 defines this value to be (0b11110 << 3)
        """
        return (self._hdr & APv6Udp.HDR_TYPE_MASK) >> APv6Udp.HDR_TYPE_SHIFT

    @property
    def hdr_co(self,):
        """Returns UDP Header's Checksum Omit flag
        """
        return (self._hdr & APv6Udp.HDR_CO_MASK) >> APv6Udp.HDR_CO_SHIFT

    @property
    def hdr_ports(self,):
        """Returns UDP Header's Ports value
        """
        return (self._hdr & APv6Udp.HDR_PORTS_MASK) >> APv6Udp.HDR_PORTS_SHIFT


    # Setters for the _hdr subfields
    @hdr_type.setter
    def hdr_type(self, val):
        """Sets the Type subfield in the header field.
        """
        assert val == APv6Udp.HDR_TYPE
        self._hdr = (self._hdr & ~APv6Udp.HDR_TYPE_MASK) | (val << APv6Udp.HDR_TYPE_SHIFT)

    @hdr_co.setter
    def hdr_co(self, val):
        """Sets the Chksum Omit subfield in the header field.
        """
        assert val < 2
        self._hdr = (self._hdr & ~APv6Udp.HDR_CO_MASK) | ((val & 1) << APv6Udp.HDR_CO_SHIFT)

    @hdr_ports.setter
    def hdr_ports(self, val):
        """Sets the Ports subfield in the header field.
        """
        assert val < 4
        self._hdr = (self._hdr & ~APv6Udp.HDR_PORTS_MASK) | ((val & 0b11) << APv6Udp.HDR_PORTS_SHIFT)


    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when an instance of this class is created
        by passing a bytes object to the constructor
        """
        super().unpack(buf) # unpacks _hdr

        if self.hdr_type != APv6Udp.HDR_TYPE:
            raise dpkt.UnpackError("Unpacking compressed UDP, but encountered wrong type value")

        if self.hdr_co == 0:
            if len(self.data) < 2:
                raise dpkt.NeedData("for UDP checksum")
            self.chksum = struct.unpack("!H", self.data[0:2])[0]
            self.data = self.data[2:]

        p = self.hdr_ports
        if p == APv6Udp.HDR_PORTS_SRC_INLN_DST_INLN:
            if len(self.data) < 4:
                raise dpkt.NeedData("for UDP ports")
            self.src_port = struct.unpack("!H", self.data[0:2])[0]
            self.dst_port = struct.unpack("!H", self.data[2:4])[0]
            self.data = self.data[4:]
        elif p == APv6Udp.HDR_PORTS_SRC_INLN_DST_F0XX:
            if len(self.data) < 3:
                raise dpkt.NeedData("for UDP ports")
            self.src_port = struct.unpack("!H", self.data[0:2])[0]
            self.dst_port = 0xf000 | self.data[2]
            self.data = self.data[3:]
        elif p == APv6Udp.HDR_PORTS_SRC_F0XX_DST_INLN:
            if len(self.data) < 3:
                raise dpkt.NeedData("for UDP ports")
            self.src_port = 0xf000 | self.data[0]
            self.dst_port = struct.unpack("!H", self.data[1:3])[0]
            self.data = self.data[3:]
        elif p == APv6Udp.HDR_PORTS_SRC_F0BX_DST_F0BX:
            if len(self.data) < 1:
                raise dpkt.NeedData("for UDP ports")
            d = self.data[0]
            self.src_port = 0xf0b0 | ((d >> 4) & 0b1111)
            self.dst_port = 0xf0b0 | (d & 0b1111)
            self.data = self.data[1:]


    def pack_hdr(self):
        """Packs header attributes into a bytes object.
        This function is called when bytes() or len() is called
        on an instance of APv6Udp.
        """
        d = bytearray()

        # Field setter functions affect _hdr value,
        # so insert _hdr at the end of this function

        if self.chksum:
            self.hdr_co = 0
            self.chksum = struct.pack("!H", self.chksum)
            d.extend(self.chksum)
        else:
            self.hdr_co = 1
            self.chksum = APv6Udp.DEFAULT_CHKSUM

        # Accept source port as int or bytes types
        # and make sure we have the bytes in src_port
        # and the int in src_port_int
        if type(self.src_port) is int:
            self.src_port_int = self.src_port
            self.src_port = struct.pack("!H", self.src_port)
        elif type(self.src_port) is bytes:
            self.src_port_int = struct.unpack("!H", self.src_port)[0]

        # Accept dest port as int or bytes types
        # and make sure we have the bytes in dst_port
        # and the int in dst_port_int
        if type(self.dst_port) is int:
            self.dst_port_int = self.dst_port
            self.dst_port = struct.pack("!H", self.dst_port)
        elif type(self.dst_port) is bytes:
            self.dst_port_int = struct.unpack("!H", self.dst_port)[0]

        if ((self.src_port_int & 0xFFF0) == 0xF0B0 and
                (self.dst_port_int & 0xFFF0) == 0xF0B0):
            self.hdr_ports = APv6Udp.HDR_PORTS_SRC_F0BX_DST_F0BX
            src_nbl = self.src_port_int & 0x000F
            dst_nbl = self.dst_port_int & 0x000F
            d.append(src_nbl << 4 | dst_nbl)

        elif (self.src_port_int & 0xFF00) == 0xF000:
            self.hdr_ports = APv6Udp.HDR_PORTS_SRC_F0XX_DST_INLN
            d.append(self.src_port_int & 0x00FF)
            d.extend(self.dst_port)

        elif (self.dst_port_int & 0xFF00) == 0xF000:
            self.hdr_ports = APv6Udp.HDR_PORTS_SRC_INLN_DST_F0XX
            d.extend(self.src_port)
            d.append(self.dst_port_int & 0x00FF)

        else:
            self.hdr_ports = APv6Udp.HDR_PORTS_SRC_INLN_DST_INLN
            d.extend(self.src_port)
            d.extend(self.dst_port)

        return super().pack_hdr() + bytes(d)
