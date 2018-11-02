#!/usr/bin/env python3


import unittest

import heymac


class TestAPv6Frame(unittest.TestCase):
    """Tests the heymac.APv6Frame packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """

    def test_min(self,):
        # Pack
        f = heymac.APv6Frame()
        b = bytes(f)
        self.assertEqual(b, b"\xD7")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 1)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0x01)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")

    def test_nhc_default(self,):
        # Pack
        f = heymac.APv6Frame(iphc_nhc=1)
        b = bytes(f)
        self.assertEqual(b, b"\xD7")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 1)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0x01)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")

    def test_nhc_uncompressed(self,):
        # Pack
        f = heymac.APv6Frame(iphc_nhc=0)
        b = bytes(f)
        # Only compressed next-headers are supported at this time
        self.assertEqual(b, b"\xD7")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        # Only compressed next-headers are supported at this time
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 1)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0x01)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")

    def test_nhc_extreme_value(self,):
        # Pack
        with self.assertRaises(AssertionError):
            f = heymac.APv6Frame(iphc_nhc=999)


    def test_hlim_1(self,):
        # Pack
        f = heymac.APv6Frame(iphc_hlim=0b01)
        b = bytes(f)
        self.assertEqual(b, b"\xD7")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 1)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0x01)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")

    def test_hlim_2(self,):
        # Pack
        f = heymac.APv6Frame(iphc_hlim=0b10)
        b = bytes(f)
        self.assertEqual(b, b"\xDB")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 2)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0x40)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")

    def test_hlim_3(self,):
        # Pack
        f = heymac.APv6Frame(iphc_hlim=0b11)
        b = bytes(f)
        self.assertEqual(b, b"\xDF")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 3)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0xFF)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")

    def test_hlim_extreme_value(self,):
        # Pack
        with self.assertRaises(AssertionError):
            f = heymac.APv6Frame(iphc_hlim=999)


    def test_sam_default(self,):
        # Pack
        f = heymac.APv6Frame(iphc_sam=1)
        b = bytes(f)
        self.assertEqual(b, b"\xD7")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 1)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0x01)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")

    def test_sam_extreme_value(self,):
        # Pack
        with self.assertRaises(AssertionError):
            f = heymac.APv6Frame(iphc_sam=999)


    def test_dam_default(self,):
        # Pack
        f = heymac.APv6Frame(iphc_dam=1)
        b = bytes(f)
        self.assertEqual(b, b"\xD7")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 1)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0x01)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")

    def test_dam_extreme_value(self,):
        # Pack
        with self.assertRaises(AssertionError):
            f = heymac.APv6Frame(iphc_dam=999)


    def test_hops_special_1(self,):
        # Pack
        f = heymac.APv6Frame(hops=b"\x01")
        b = bytes(f)
        self.assertEqual(b, b"\xD7")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 1)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0x01)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")

    def test_hops_special_64(self,):
        # Pack
        f = heymac.APv6Frame(hops=b"\x40")
        b = bytes(f)
        self.assertEqual(b, b"\xDB")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 2)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0x40)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")

    def test_hops_special_255(self,):
        # Pack
        f = heymac.APv6Frame(hops=b"\xFF")
        b = bytes(f)
        self.assertEqual(b, b"\xDF")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 3)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0xFF)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")

    def test_hops_2(self,):
        # Pack
        f = heymac.APv6Frame(hops=b"\x02")
        b = bytes(f)
        self.assertEqual(b, b"\xD3\x02")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 0)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0x02)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")

    def test_hops_32(self,):
        # Pack
        f = heymac.APv6Frame(hops=b"\x20")
        b = bytes(f)
        self.assertEqual(b, b"\xD3\x20")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 0)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0x20)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"")


    def test_src_addr(self,):
        # Pack
        f = heymac.APv6Frame(src=b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        b = bytes(f)
        self.assertEqual(b, b"\xD5\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 1)
        self.assertEqual(f.iphc_sam, 0)
        self.assertEqual(f.iphc_dam, 1)
        self.assertEqual(f.hops, 0x01)
        self.assertEqual(f.src, b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        self.assertEqual(f.dst, b"")


    def test_dst_addr(self,):
        # Pack
        f = heymac.APv6Frame(dst=b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        b = bytes(f)
        self.assertEqual(b, b"\xD6\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 1)
        self.assertEqual(f.iphc_sam, 1)
        self.assertEqual(f.iphc_dam, 0)
        self.assertEqual(f.hops, 0x01)
        self.assertEqual(f.src, b"")
        self.assertEqual(f.dst, b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")


    def test_src_dst_addrs(self,):
        # Pack
        f = heymac.APv6Frame(
                src=b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f",
                dst=b"\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")
        b = bytes(f)
        self.assertEqual(b, b"\xD4\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 1)
        self.assertEqual(f.iphc_sam, 0)
        self.assertEqual(f.iphc_dam, 0)
        self.assertEqual(f.hops, 0x01)
        self.assertEqual(f.src, b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        self.assertEqual(f.dst, b"\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")


    def test_hops_src_dst_addrs(self,):
        # Pack
        f = heymac.APv6Frame(
                hops=b"\x33",
                src=b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f",
                dst=b"\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")
        b = bytes(f)
        self.assertEqual(b, b"\xD0\x33\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 0)
        self.assertEqual(f.iphc_sam, 0)
        self.assertEqual(f.iphc_dam, 0)
        self.assertEqual(f.hops, 0x33)
        self.assertEqual(f.src, b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        self.assertEqual(f.dst, b"\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")


    def test_regression_hops_from_int(self,):
        """Allow hops to be given as an int
        """
        # Pack
        f = heymac.APv6Frame(
                hops=0x33,
                src=b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f",
                dst=b"\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")
        b = bytes(f)
        self.assertEqual(b, b"\xD0\x33\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")
        # Unpack
        f = heymac.APv6Frame(b)
        self.assertEqual(f.iphc_prefix, 6)
        self.assertEqual(f.iphc_nhc, 1)
        self.assertEqual(f.iphc_hlim, 0)
        self.assertEqual(f.iphc_sam, 0)
        self.assertEqual(f.iphc_dam, 0)
        self.assertEqual(f.hops, 0x33)
        self.assertEqual(f.src, b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f")
        self.assertEqual(f.dst, b"\xD0\xD1\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9\xDa\xDb\xDc\xDd\xDe\xDf")


if __name__ == "__main__":
    unittest.main()
