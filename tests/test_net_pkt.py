#!/usr/bin/env python3


import unittest

from heymac.net import APv6Packet, APv6PacketError


class TestAPv6Packet(unittest.TestCase):
    """Tests the APv6Packet packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """

    def test_min(self):
        p = APv6Packet()
        b = bytes(p)
        self.assertEqual(b, b"\xD7")
        p = APv6Packet.parse(b)
        self.assertEqual(p.hdr, b"\xD7")
        self.assertEqual(p.hops, b"\x01")
        self.assertEqual(p.saddr, b"")
        self.assertEqual(p.daddr, b"")

    def test_hlim_1(self):
        p = APv6Packet(hops=1)
        b = bytes(p)
        self.assertEqual(b, b"\xD7")
        p = APv6Packet.parse(b)
        self.assertEqual(p.hdr, b"\xD7")
        self.assertEqual(p.hops, b"\x01")
        self.assertEqual(p.saddr, b"")
        self.assertEqual(p.daddr, b"")

    def test_hlim_42(self):
        p = APv6Packet(hops=42)
        b = bytes(p)
        self.assertEqual(b, b"\xD3\x2A")
        p = APv6Packet.parse(b)
        self.assertEqual(p.hdr, b"\xD3")
        self.assertEqual(p.hops, b"\x2A")
        self.assertEqual(p.saddr, b"")
        self.assertEqual(p.daddr, b"")

    def test_hlim_64(self):
        p = APv6Packet(hops=64)
        b = bytes(p)
        self.assertEqual(b, b"\xDB")
        p = APv6Packet.parse(b)
        self.assertEqual(p.hdr, b"\xDB")
        self.assertEqual(p.hops, b"\x40")
        self.assertEqual(p.saddr, b"")
        self.assertEqual(p.daddr, b"")

    def test_hlim_255(self):
        p = APv6Packet(hops=255)
        b = bytes(p)
        self.assertEqual(b, b"\xDF")
        p = APv6Packet.parse(b)
        self.assertEqual(p.hdr, b"\xDF")
        self.assertEqual(p.hops, b"\xFF")
        self.assertEqual(p.saddr, b"")
        self.assertEqual(p.daddr, b"")

    def test_hlim_extreme_value(self):
        with self.assertRaises(APv6PacketError):
            p = APv6Packet(hops=999)


    def test_saddr(self):
        p = APv6Packet(saddr=b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        b = bytes(p)
        self.assertEqual(b, b"\xD5\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        p = APv6Packet.parse(b)
        self.assertEqual(p.hdr, b"\xD5")
        self.assertEqual(p.hops, b"\x01")
        self.assertEqual(p.saddr, b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        self.assertEqual(p.daddr, b"")


    def test_daddr(self):
        p = APv6Packet(daddr=b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        b = bytes(p)
        self.assertEqual(b, b"\xD6\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        p = APv6Packet.parse(b)
        self.assertEqual(p.hdr, b"\xD6")
        self.assertEqual(p.hops, b"\x01")
        self.assertEqual(p.saddr, b"")
        self.assertEqual(p.daddr, b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")


    def test_saddr_daddr(self):
        p = APv6Packet(
            saddr=b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f",
            daddr=b"\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")
        b = bytes(p)
        self.assertEqual(b, b"\xD4\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")
        p = APv6Packet.parse(b)
        self.assertEqual(p.hdr, b"\xD4")
        self.assertEqual(p.hops, b"\x01")
        self.assertEqual(p.saddr, b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        self.assertEqual(p.daddr, b"\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")


    def test_hops_saddr_daddr(self):
        p = APv6Packet(
            hops=b"\x33",
            saddr=b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f",
            daddr=b"\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")
        b = bytes(p)
        self.assertEqual(b, b"\xD0\x33\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")
        p = APv6Packet.parse(b)
        self.assertEqual(p.hops, b"\x33")
        self.assertEqual(p.saddr, b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        self.assertEqual(p.daddr, b"\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")


if __name__ == "__main__":
    unittest.main()
