#!/usr/bin/env python3


import unittest

from heymac.lnk import HeymacFrame, HeymacFrameError


class TestHeyMacFrame(unittest.TestCase):
    """Tests the HeymacFrame building and serializing.
    """

    def test_mac(self):
        # Build and serialize
        f = HeymacFrame(
            HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
            0)
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x00")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertTrue(f.is_heymac())
        self.assertEqual(f.fctl, 0)
        self.assertIsNone(f.netid)
        self.assertIsNone(f.daddr)
        self.assertIsNone(f.saddr)
        self.assertIsNone(f.payld)
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_not_mac(self):
        b = b"\x00\x00"
        # Parse and test
        # expect that parser raises an exception due to invalid frame header
        self.assertRaises(HeymacFrameError, HeymacFrame.parse, b)


    def test_csma(self):
        # Build and serialize
        f = HeymacFrame(
            HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
            0)
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x00")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.fctl, 0x00)
        self.assertIsNone(f.netid)
        self.assertIsNone(f.daddr)
        self.assertIsNone(f.saddr)
        self.assertIsNone(f.payld)
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_min_payld(self):
        # Build and serialize
        f = HeymacFrame(
            HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
            0)
        f.payld = b"ABCD"
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x00ABCD")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.fctl, 0)
        self.assertIsNone(f.netid)
        self.assertIsNone(f.daddr)
        self.assertIsNone(f.saddr)
        self.assertEqual(f.payld, b"ABCD")
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_saddr64b(self):
        # Build and serialize
        f = HeymacFrame(
            HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
            HeymacFrame.FCTL_L | HeymacFrame.FCTL_S)
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x44\x01\x02\x03\x04\x05\x06\x07\x08")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.fctl, 0x44)
        self.assertIsNone(f.netid)
        self.assertIsNone(f.daddr)
        self.assertEqual(
            f.saddr,
            b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertIsNone(f.payld)
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_saddr64b_daddr64b(self):
        # Build and serialize
        f = HeymacFrame(
            HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
            HeymacFrame.FCTL_L | HeymacFrame.FCTL_D | HeymacFrame.FCTL_S)
        f.daddr = b"\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8"
        f.saddr = b"\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8"
        f.payld = b"hi"
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x54\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8hi")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.fctl, 0x54)
        self.assertIsNone(f.netid)
        self.assertEqual(f.daddr, b"\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8")
        self.assertEqual(f.saddr, b"\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8")
        self.assertEqual(f.payld, b"hi")
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_saddr16b_daddr16b(self):
        # Build and serialize
        f = HeymacFrame(
            HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
            HeymacFrame.FCTL_S | HeymacFrame.FCTL_D)
        f.daddr = b"\xd1\xd2"
        f.saddr = b"\xc1\xc2"
        f.payld = b"hello world"
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x14\xd1\xd2\xc1\xc2hello world")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.fctl, 0x14)
        self.assertIsNone(f.netid)
        self.assertEqual(f.daddr, b"\xd1\xd2")
        self.assertEqual(f.saddr, b"\xc1\xc2")
        self.assertEqual(f.payld, b"hello world")
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_netid_daddr(self):
        # Build and serialize
        f = HeymacFrame(
            HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
            HeymacFrame.FCTL_N | HeymacFrame.FCTL_D)
        f.netid = b"\x80\xA5"
        f.daddr = b"\xd1\xd2"
        f.payld = b"data"
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x30\x80\xa5\xd1\xd2data")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.fctl, 0x30)
        self.assertEqual(f.netid, b"\x80\xA5")
        self.assertEqual(f.daddr, b"\xd1\xd2")
        self.assertIsNone(f.saddr)
        self.assertEqual(f.payld, b"data")
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


if __name__ == '__main__':
    unittest.main()
