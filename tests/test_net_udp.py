#!/usr/bin/env python3


import unittest

from heymac.net import UdpDatagram, UdpDatagramError


class TestUdpDatagram(unittest.TestCase):
    """Tests the UdpDatagram packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """

    def test_min(self):
        f = UdpDatagram(
            src_port=0xF0B0,
            dst_port=0xF0B0)
        b = bytes(f)
        self.assertEqual(b, b"\xF7\x00")
        f = UdpDatagram.parse(b)
        self.assertEqual(f.hdr, b"\xF7")
        self.assertEqual(f.src_port, b"\xF0\xB0")
        self.assertEqual(f.dst_port, b"\xF0\xB0")

    def test_src_port_f0b3(self):
        f = UdpDatagram(
            src_port=0xF0B3,
            dst_port=0xF0B0)
        b = bytes(f)
        self.assertEqual(b, b"\xF7\x30")
        f = UdpDatagram.parse(b)
        self.assertEqual(f.hdr, b"\xF7")
        self.assertEqual(f.src_port, b"\xF0\xB3")
        self.assertEqual(f.dst_port, b"\xF0\xB0")

    def test_src_port_f009(self):
        f = UdpDatagram(
            src_port=0xF009,
            dst_port=0xF0B0)
        b = bytes(f)
        self.assertEqual(b, b"\xF6\x09\xF0\xB0")
        f = UdpDatagram.parse(b)
        self.assertEqual(f.hdr, b"\xF6")
        self.assertEqual(f.src_port, b"\xF0\x09")
        self.assertEqual(f.dst_port, b"\xF0\xB0")

    def test_src_port_abcd(self):
        f = UdpDatagram(
            src_port=0xABCD,
            dst_port=0xF0B0)
        b = bytes(f)
        self.assertEqual(b, b"\xF5\xAB\xCD\xB0")
        f = UdpDatagram.parse(b)
        self.assertEqual(f.hdr, b"\xF5")
        self.assertEqual(f.src_port, b"\xAB\xCD")
        self.assertEqual(f.dst_port, b"\xF0\xB0")

    def test_dst_port_f009(self):
        f = UdpDatagram(
            src_port=0xF0B0,
            dst_port=0xF009)
        b = bytes(f)
        self.assertEqual(b, b"\xF6\xB0\xF0\x09")
        f = UdpDatagram.parse(b)
        self.assertEqual(f.hdr, b"\xF6")
        self.assertEqual(f.src_port, b"\xF0\xB0")
        self.assertEqual(f.dst_port, b"\xF0\x09")

    def test_dst_port_abcd(self):
        f = UdpDatagram(
            src_port=0xF0B0,
            dst_port=0xABCD)
        b = bytes(f)
        self.assertEqual(b, b"\xF6\xB0\xAB\xCD")
        f = UdpDatagram.parse(b)
        self.assertEqual(f.hdr, b"\xF6")
        self.assertEqual(f.src_port, b"\xF0\xB0")
        self.assertEqual(f.dst_port, b"\xAB\xCD")


    def test_insufficient_data(self):
        """Test cases that should raise exceptions"""
        with self.assertRaises(UdpDatagramError):
            f = UdpDatagram.parse(b"")


    def test_regression_serialize_twice(self):
        """Test serialization can happen more than one time"""
        f = UdpDatagram(
            src_port=0x1112,
            dst_port=0xF0B0)
        b1 = bytes(f)
        b2 = bytes(f)


if __name__ == "__main__":
    unittest.main()
