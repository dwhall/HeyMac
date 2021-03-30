#!/usr/bin/env python3


import unittest

import heymac


class TestAPv6Udp(unittest.TestCase):
    """Tests the heymac.APv6Udp packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """

    def test_min(self):
        # Pack
        f = heymac.APv6Udp(
            src_port=0xF0B0,
            dst_port=0xF0B0)
        b = bytes(f)
        self.assertEqual(b, b"\xF7\x00")
        # Unpack
        f = heymac.APv6Udp(b)
        self.assertEqual(f.hdr_type, 0b11110)
        self.assertEqual(f.hdr_co, 1)
        self.assertEqual(f.hdr_ports, 0b11)
        self.assertEqual(f.chksum, b"")
        self.assertEqual(f.src_port, 0xF0B0)
        self.assertEqual(f.dst_port, 0xF0B0)

    def test_chksum(self):
        # Pack
        f = heymac.APv6Udp(
            chksum=0x2A3B,
            src_port=0xF0B0,
            dst_port=0xF0B0)
        b = bytes(f)
        self.assertEqual(b, b"\xF3\x2A\x3B\x00")
        # Unpack
        f = heymac.APv6Udp(b)
        self.assertEqual(f.hdr_type, 0b11110)
        self.assertEqual(f.hdr_co, 0)
        self.assertEqual(f.hdr_ports, 0b11)
        self.assertEqual(f.chksum, 0x2A3B)
        self.assertEqual(f.src_port, 0xF0B0)
        self.assertEqual(f.dst_port, 0xF0B0)

    def test_src_port_f0b3(self):
        # Pack
        f = heymac.APv6Udp(
            src_port=0xF0B3,
            dst_port=0xF0B0)
        b = bytes(f)
        self.assertEqual(b, b"\xF7\x30")
        # Unpack
        f = heymac.APv6Udp(b)
        self.assertEqual(f.hdr_type, 0b11110)
        self.assertEqual(f.hdr_co, 1)
        self.assertEqual(f.hdr_ports, 0b11)
        self.assertEqual(f.chksum, b"")
        self.assertEqual(f.src_port, 0xF0B3)
        self.assertEqual(f.dst_port, 0xF0B0)

    def test_src_port_f009(self):
        # Pack
        f = heymac.APv6Udp(
            src_port=0xF009,
            dst_port=0xF0B0)
        b = bytes(f)
        self.assertEqual(b, b"\xF6\x09\xF0\xB0")
        # Unpack
        f = heymac.APv6Udp(b)
        self.assertEqual(f.hdr_type, 0b11110)
        self.assertEqual(f.hdr_co, 1)
        self.assertEqual(f.hdr_ports, 0b10)
        self.assertEqual(f.chksum, b"")
        self.assertEqual(f.src_port, 0xF009)
        self.assertEqual(f.dst_port, 0xF0B0)

    def test_src_port_abcd(self):
        # Pack
        f = heymac.APv6Udp(
            src_port=0xABCD,
            dst_port=0xF0B0)
        b = bytes(f)
        self.assertEqual(b, b"\xF5\xAB\xCD\xB0")
        # Unpack
        f = heymac.APv6Udp(b)
        self.assertEqual(f.hdr_type, 0b11110)
        self.assertEqual(f.hdr_co, 1)
        self.assertEqual(f.hdr_ports, 0b01)
        self.assertEqual(f.chksum, b"")
        self.assertEqual(f.src_port, 0xABCD)
        self.assertEqual(f.dst_port, 0xF0B0)

    def test_dst_port_f009(self):
        # Pack
        f = heymac.APv6Udp(
            src_port=0xF0B0,
            dst_port=0xF009)
        b = bytes(f)
        self.assertEqual(b, b"\xF6\xB0\xF0\x09")
        # Unpack
        f = heymac.APv6Udp(b)
        self.assertEqual(f.hdr_type, 0b11110)
        self.assertEqual(f.hdr_co, 1)
        self.assertEqual(f.hdr_ports, 0b10)
        self.assertEqual(f.chksum, b"")
        self.assertEqual(f.src_port, 0xF0B0)
        self.assertEqual(f.dst_port, 0xF009)

    def test_dst_port_abcd(self):
        # Pack
        f = heymac.APv6Udp(
            src_port=0xF0B0,
            dst_port=0xABCD)
        b = bytes(f)
        self.assertEqual(b, b"\xF6\xB0\xAB\xCD")
        # Unpack
        f = heymac.APv6Udp(b)
        self.assertEqual(f.hdr_type, 0b11110)
        self.assertEqual(f.hdr_co, 1)
        self.assertEqual(f.hdr_ports, 0b10)
        self.assertEqual(f.chksum, b"")
        self.assertEqual(f.src_port, 0xF0B0)
        self.assertEqual(f.dst_port, 0xABCD)

    def test_chksum_src_dst(self):
        # Pack
        f = heymac.APv6Udp(
            chksum=0xC1C2,
            src_port=0x1112,
            dst_port=0x2122)
        b = bytes(f)
        self.assertEqual(b, b"\xF0\xC1\xC2\x11\x12\x21\x22")
        # Unpack
        f = heymac.APv6Udp(b)
        self.assertEqual(f.hdr_type, 0b11110)
        self.assertEqual(f.hdr_co, 0)
        self.assertEqual(f.hdr_ports, 0b00)
        self.assertEqual(f.chksum, 0xC1C2)
        self.assertEqual(f.src_port, 0x1112)
        self.assertEqual(f.dst_port, 0x2122)

    def test_regression_serialize_without_port(self):
        """An assertion should be thrown if
        the coder does not give src/dst ports
        """
        import struct
        f = heymac.APv6Udp()
        with self.assertRaises(struct.error):
            b = bytes(f)
        f = heymac.APv6Udp(src_port=0x1234)
        with self.assertRaises(struct.error):
            b = bytes(f)
        f = heymac.APv6Udp(dst_port=0x1234)
        with self.assertRaises(struct.error):
            b = bytes(f)


    def test_regression_serialize_twice(self):
        """Problem: serializing an APv6Udp() a second time
        caused an assertion::

            >>> u = heymac.APv6Udp()
            >>> u.src_port = 0xF0B1
            >>> print(u)
            b'\xf7\x10'
            >>> u.dst_port = 0xF0B9
            >>> print(u)
            Traceback (most recent call last):
            ...<snip>...
            struct.error: required argument is not an integer
        """
        # Pack
        f = heymac.APv6Udp(
            src_port = 0x1112,
            dst_port=0xF0B0)
        b1 = bytes(f)
        f.dst_port = 0x2122
        b2 = bytes(f)


    def test_regression_give_chksum_as_bytes(self):
        f = heymac.APv6Udp(
            src_port=0x1234,
            dst_port=0x5678,
            chksum=b"\x9A\xBC")
        b = bytes(f)


if __name__ == "__main__":
    unittest.main()
