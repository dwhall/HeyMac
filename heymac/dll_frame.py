import logging
import struct

import dpkt # pip install dpkt


# APv6 protocol version
APV6_VERSION = 1
APV6_PREFIX = 0xC0


class APv6Frame(dpkt.Packet):
    """APv6 frame definition
    """
    __byte_order__ = '!' # Network order
    __hdr__ = (
        # The underscore prefix means do not access that field directly.
        # Access properties .iphc, .iphc_nh, etc. instead.
        ('_iphc', 'B', APV6_PREFIX),
#        ('_ver_seq', '0s', b''),
    )

    IPHC_NH_MASK = 0b00010000
    IPHC_HLIM_MASK = 0b00001100
    IPHC_SAM_MASK = 0b00000010
    IPHC_DAM_MASK = 0b00000001

    IPHC_NH_SHIFT = 4
    IPHC_HLIM_SHIFT = 2
    IPHC_SAM_SHIFT = 1
    IPHC_DAM_SHIFT = 0

    # Getters for the _iphc subfields
    @property
    def iphc(self,):
        """Gets the full value (all bits) from the IPHC field.
        """
        return self._iphc

    @property
    def iphc_nh(self,):
        """Returns bit pattern to indicate Next Header compressed.
        0: Next Header is carried in-line
        1: Next Header is encoded via LOWPAN_NHC
        """
        return (self._iphc & IPHC_NH_MASK) >> IPHC_NH_SHIFT

    @property
    def iphc_hlim(self,):
        """Returns the bit pattern to indicate the Hop Limit
        0: Hop Limit is carried in-line
        1: Hop Limit is 1
        2: Hop Limit is 64
        3: Hop Limit is 255
        """
        return (self._iphc & IPHC_HLIM_MASK) >> IPHC_HLIM_SHIFT

    @property
    def iphc_sam(self,):
        """Returns bit pattern to indicate Source Address mode.
        0: Src Addr is carried in-line
        1: Src Addr is elided; computed from MAC layer
        """
        return (self._iphc & IPHC_SAM_MASK) >> IPHC_SAM_SHIFT

    @property
    def iphc_dam(self,):
        """Returns bit pattern to indicate Destination Address mode.
        0: Dest Addr is carried in-line
        1: Dest Addr is elided; computed from MAC layer
        """
        return (self._iphc & IPHC_DAM_MASK) >> IPHC_DAM_SHIFT


class APv6Udp(APv6Frame):
    """APv6 UDP packet definition
    Derived from RFC6282
    """
    APV6_UDP_HDR_TYPE = 0xF0

    HDR_TYPE_MASK = 0b11111000
    HDR_ENC_CO_MASK = 0b00000010
    HDR_ENC_PORTS_MASK = 0b00000011

    HDR_TYPE_SHIFT = 3
    HDR_ENC_CO_SHIFT = 1
    HDR_ENC_PORTS_SHIFT = 0

    __hdr__ = (
        # The underscore prefix means do not access that field directly.
        # Access properties .hdr_co and .hdr_ports, instead.
        ('_iphc', 'B', APV6_PREFIX),
        ('_hdr_enc', 'B', APV6_UDP_HDR_TYPE), # RFC6282 4.3.3.  UDP LOWPAN_NHC Format
        # Fields below this are optional or variable-length
        ('chksum', '0s', b''),
        ('src_port', '0s', b''),
        ('dst_port', '0s', b''),
    )

    @property
    def hdr_co(self,):
        """Returns UDP Header's Checksum Omit flag
        """
        return (self._hdr_enc & HDR_ENC_CO_MASK) >> HDR_ENC_CO_SHIFT

    @property
    def hdr_ports(self,):
        """Returns UDP Header's Ports value
        """
        return (self._hdr_enc & HDR_ENC_PORTS_MASK) >> HDR_ENC_PORTS_SHIFT


    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when an instance of this class is created
        by passing a bytes object to the constructor
        """
        super().unpack(buf)

        # TODO: raise a dpkt exception:
        assert self._hdr_enc & HDR_TYPE_MASK == APV6_UDP_HDR_TYPE

        if self.hdr_co == 0:
            self.chksum = self.data[0:2]
            self.data = self.data[2:]

        p = self.hdr_ports
        if p in 0b00:
            self.src_port = self.data[0:2]
            self.dst_port = self.data[2:4]
            self.data = self.data[4:]
        elif p == 0b01:
            self.src_port = self.data[0:2]
            self.dst_port = 0xf000 | self.data[2]
            self.data = self.data[3:]
        elif p == 0b10:
            self.src_port = 0xf000 | self.data[0]
            self.dst_port = self.data[1:3]
            self.data = self.data[3:]
        elif p == 0b11:
            d = self.data[0]
            self.src_port = 0xf0b0 | ((d >> 4) & 0b1111)
            self.dst_port = 0xf0b0 | (d & 0b1111)
            self.data = self.data[1:]


    def pack_hdr(self):
        """Packs header attributes into a bytes object.
        This function is called when bytes() or len() is called
        on an instance of APv6Udp.
        """
        super().pack_hdr()

        d = bytearray()
        nbytes = 0

        if hasattr(self, "chksum"):
            pass
