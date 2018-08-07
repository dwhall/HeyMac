import logging
import struct

import dpkt # pip install dpkt


# APv6 protocol version
APV6_VERSION = 1


class APv6Frame(dpkt.Packet):
    """APv6 frame definition
    """
    IPHC_PREFIX_MASK = 0b11100000
    IPHC_NH_MASK = 0b00010000
    IPHC_HLIM_MASK = 0b00001100
    IPHC_SAM_MASK = 0b00000010
    IPHC_DAM_MASK = 0b00000001

    IPHC_PREFIX_SHIFT = 5
    IPHC_NH_SHIFT = 4
    IPHC_HLIM_SHIFT = 2
    IPHC_SAM_SHIFT = 1
    IPHC_DAM_SHIFT = 0

    APV6_PREFIX = 0b110 << IPHC_PREFIX_SHIFT


    __byte_order__ = '!' # Network order
    __hdr__ = (
        # The underscore prefix means do not access that field directly.
        # Access properties .iphc, .iphc_nh, etc. instead.
        ('_iphc', 'B', APV6_PREFIX),
    )


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
        return (self._iphc & APv6Frame.IPHC_NH_MASK) >> APv6Frame.IPHC_NH_SHIFT

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
        assert val & APv6Frame.IPHC_PREFIX_MASK == APV6_PREFIX, "Invalid APv6 prefix"
        self._iphc = 0xFF & val

    @iphc_nh.setter
    def iphc_nh(self, val):
        """Sets the Next Header bit in the IPHC field to the given value
        """
        self._iphc = (self._iphc & ~APv6Frame.IPHC_NH_MASK) | ((val & 1) << APv6Frame.IPHC_NH_SHIFT)

    @iphc_hlim.setter
    def iphc_hlim(self, val):
        """Sets the Next Header bit in the IPHC field to the given value
        """
        self._iphc = (self._iphc & ~APv6Frame.IPHC_HLIM_MASK) | ((val & 0b11) << APv6Frame.IPHC_HLIM_SHIFT)

    @iphc_sam.setter
    def iphc_sam(self, val):
        """Sets the Next Header bit in the IPHC field to the given value
        """
        self._iphc = (self._iphc & ~APv6Frame.IPHC_SAM_MASK) | ((val & 1) << APv6Frame.IPHC_SAM_SHIFT)

    @iphc_dam.setter
    def iphc_dam(self, val):
        """Sets the Next Header bit in the IPHC field to the given value
        """
        self._iphc = (self._iphc & ~APv6Frame.IPHC_DAM_MASK) | ((val & 1) << APv6Frame.IPHC_DAM_SHIFT)


class APv6Udp(APv6Frame):
    """APv6 UDP packet definition
    Inherits from APv6Frame in order to re-use setters/getters for the IPHC byte.
    Derived from RFC6282
    """
    APV6_UDP_HDR_TYPE = 0xF0

    HDR_TYPE_MASK = 0b11111000
    HDR_ENC_CO_MASK = 0b00000100
    HDR_ENC_PORTS_MASK = 0b00000011

    HDR_TYPE_SHIFT = 3
    HDR_ENC_CO_SHIFT = 2
    HDR_ENC_PORTS_SHIFT = 0

    __hdr__ = (
        # The underscore prefix means do not access that field directly.
        # Access properties .hdr_co and .hdr_ports, instead.
        ('_iphc', 'B', APv6Frame.APV6_PREFIX),
        ('_hdr_enc', 'B', APV6_UDP_HDR_TYPE), # RFC6282 4.3.3.  UDP LOWPAN_NHC Format
        # Fields below this are optional or variable-length
        ('chksum', '0s', b''),
        ('src_port', '0s', b''),
        ('dst_port', '0s', b''),
    )

    # Getters of _hdr_enc
    @property
    def hdr_co(self,):
        """Returns UDP Header's Checksum Omit flag
        """
        return (self._hdr_enc & APv6Udp.HDR_ENC_CO_MASK) >> APv6Udp.HDR_ENC_CO_SHIFT

    @property
    def hdr_ports(self,):
        """Returns UDP Header's Ports value
        """
        return (self._hdr_enc & APv6Udp.HDR_ENC_PORTS_MASK) >> APv6Udp.HDR_ENC_PORTS_SHIFT


    def unpack(self, buf):
        """Unpacks a bytes object into component attributes.
        This function is called when an instance of this class is created
        by passing a bytes object to the constructor
        """
        super().unpack(buf)

        # TODO: raise a dpkt exception:
        assert self._hdr_enc & APv6Udp.HDR_TYPE_MASK == APv6Udp.APV6_UDP_HDR_TYPE

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


if __name__ == "__main__":
    import unittest
    class TestAPv6Frame(unittest.TestCase):
        def test_min(self,):
            # Pack
            f = APv6Frame()
            b = bytes(f)
            self.assertEqual(b, b"\xC0")
            # Unpack
            f = APv6Frame(b)
            self.assertEqual(f.iphc, 0xC0)
            self.assertEqual(f.iphc_nh, 0)
            self.assertEqual(f.iphc_hlim, 0)
            self.assertEqual(f.iphc_sam, 0)
            self.assertEqual(f.iphc_dam, 0)

        def test_nh(self,):
            # Pack
            f = APv6Frame(iphc_nh=1)
            b = bytes(f)
            self.assertEqual(b, b"\xD0")
            # Unpack
            f = APv6Frame(b)
            self.assertEqual(f.iphc, 0xD0)
            self.assertEqual(f.iphc_nh, 1)
            self.assertEqual(f.iphc_hlim, 0)
            self.assertEqual(f.iphc_sam, 0)
            self.assertEqual(f.iphc_dam, 0)

        def test_hlim(self,):
            # Pack
            f = APv6Frame(iphc_hlim=0b11)
            b = bytes(f)
            self.assertEqual(b, b"\xCC")
            # Unpack
            f = APv6Frame(b)
            self.assertEqual(f.iphc, 0xCC)
            self.assertEqual(f.iphc_nh, 0)
            self.assertEqual(f.iphc_hlim, 3)
            self.assertEqual(f.iphc_sam, 0)
            self.assertEqual(f.iphc_dam, 0)

        def test_sam(self,):
            # Pack
            f = APv6Frame(iphc_sam=1)
            b = bytes(f)
            self.assertEqual(b, b"\xC2")
            # Unpack
            f = APv6Frame(b)
            self.assertEqual(f.iphc, 0xC2)
            self.assertEqual(f.iphc_nh, 0)
            self.assertEqual(f.iphc_hlim, 0)
            self.assertEqual(f.iphc_sam, 1)
            self.assertEqual(f.iphc_dam, 0)

        def test_dam(self,):
            # Pack
            f = APv6Frame(iphc_dam=1)
            b = bytes(f)
            self.assertEqual(b, b"\xC1")
            # Unpack
            f = APv6Frame(b)
            self.assertEqual(f.iphc, 0xC1)
            self.assertEqual(f.iphc_nh, 0)
            self.assertEqual(f.iphc_hlim, 0)
            self.assertEqual(f.iphc_sam, 0)
            self.assertEqual(f.iphc_dam, 1)

    unittest.main()

