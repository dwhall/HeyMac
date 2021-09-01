#!/usr/bin/env python3


import unittest

from heymac.lnk import *


class TestHeyMacFrame(unittest.TestCase):
    """Tests the HeymacFrame building and serializing.
    """

    def test_mac(self):
        f = HeymacFrame(HeymacFramePidType.CSMA)
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x00")

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

        # expect that parser raises an exception due to invalid frame header
        self.assertRaises(HeymacFrameError, HeymacFrame.parse, b)


    def test_csma(self):
        f = HeymacFrame(HeymacFramePidType.CSMA)
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x00")

        f = HeymacFrame.parse(b)
        self.assertEqual(f.fctl, 0x00)
        self.assertIsNone(f.netid)
        self.assertIsNone(f.daddr)
        self.assertIsNone(f.saddr)
        self.assertIsNone(f.payld)
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_min_payld(self):
        f = HeymacFrame(HeymacFramePidType.CSMA)
        f.payld = HeymacCmdTxt(FLD_MSG=b"ABCD")
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x00\x83ABCD")

        f = HeymacFrame.parse(b)
        self.assertEqual(f.fctl, 0)
        self.assertIsNone(f.netid)
        self.assertIsNone(f.daddr)
        self.assertIsNone(f.saddr)
        self.assertIsInstance(f.payld, HeymacCmdTxt)
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_saddr64b(self):
        f = HeymacFrame(HeymacFramePidType.CSMA)
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x44\x01\x02\x03\x04\x05\x06\x07\x08")

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
        f = HeymacFrame(HeymacFramePidType.CSMA)
        f.daddr = b"\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8"
        f.saddr = b"\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8"
        f.payld = HeymacCmdTxt(FLD_MSG=b"hi")
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x54\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\x83hi")

        f = HeymacFrame.parse(b)
        self.assertEqual(f.fctl, 0x54)
        self.assertIsNone(f.netid)
        self.assertEqual(f.daddr, b"\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8")
        self.assertEqual(f.saddr, b"\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8")
        self.assertIsInstance(f.payld, HeymacCmdTxt)
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_saddr16b_daddr16b(self):
        f = HeymacFrame(HeymacFramePidType.CSMA)
        f.daddr = b"\xd1\xd2"
        f.saddr = b"\xc1\xc2"
        f.payld = HeymacCmdTxt(FLD_MSG=b"hello world")
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x14\xd1\xd2\xc1\xc2\x83hello world")

        f = HeymacFrame.parse(b)
        self.assertEqual(f.fctl, 0x14)
        self.assertIsNone(f.netid)
        self.assertEqual(f.daddr, b"\xd1\xd2")
        self.assertEqual(f.saddr, b"\xc1\xc2")
        self.assertIsInstance(f.payld, HeymacCmdTxt)
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_netid_daddr(self):
        f = HeymacFrame(HeymacFramePidType.CSMA)
        f.netid = b"\x80\xA5"
        f.daddr = b"\xd1\xd2"
        f.payld = HeymacCmdTxt(FLD_MSG=b"data")
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x30\x80\xa5\xd1\xd2\x83data")

        f = HeymacFrame.parse(b)
        self.assertEqual(f.fctl, 0x30)
        self.assertEqual(f.netid, b"\x80\xA5")
        self.assertEqual(f.daddr, b"\xd1\xd2")
        self.assertIsNone(f.saddr)
        self.assertIsInstance(f.payld, HeymacCmdTxt)
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_saddr16b_daddr16b_arg(self):
        f = HeymacFrame(HeymacFramePidType.CSMA,
                        daddr=b"\xd1\xd2",
                        saddr=b"\xc1\xc2",
                        payld=HeymacCmdTxt(FLD_MSG=b"hello world"))
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x14\xd1\xd2\xc1\xc2\x83hello world")

        f = HeymacFrame.parse(b)
        self.assertEqual(f.fctl, 0x14)
        self.assertIsNone(f.netid)
        self.assertEqual(f.daddr, b"\xd1\xd2")
        self.assertEqual(f.saddr, b"\xc1\xc2")
        self.assertIsInstance(f.payld, HeymacCmdTxt)
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def _test_invalid_field(self):
        f = HeymacFrame(HeymacFramePidType.CSMA,
                        daddr=b"\xd1\xd2",
                        saddr=b"\xc1\xc2",
                        timmy=b"timmy")

    def test_invalid_field(self):
        self.assertRaises(HeymacFrameError, self._test_invalid_field)


    def test_hie(self):
        f = HeymacFrame(HeymacFramePidType.CSMA,
                        ies=HeymacIeSequence(
                            HeymacHIeSqncNmbr(42),
                            HeymacHIeTerm(),
                            HeymacPIeTerm()))
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x08\x81\x00\x2A\x00\x20")

        f = HeymacFrame.parse(b)
        self.assertTrue(f.is_heymac())
        self.assertEqual(f.fctl, 0x08)
        self.assertIsNone(f.netid)
        self.assertIsNone(f.daddr)
        self.assertEqual(type(f.ies), bytes)
        self.assertIsNone(f.saddr)
        self.assertIsNone(f.payld)
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_pie(self):
        f = HeymacFrame(HeymacFramePidType.CSMA,
                        ies=HeymacIeSequence(
                            HeymacPIeMic(5, 4),
                            HeymacPIeTerm()))
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x08\xA3\x05\x04\x20")

        f = HeymacFrame.parse(b)
        self.assertTrue(f.is_heymac())
        self.assertEqual(f.fctl, 0x08)
        self.assertIsNone(f.netid)
        self.assertIsNone(f.daddr)
        self.assertEqual(type(f.ies), bytes)
        self.assertIsNone(f.saddr)
        self.assertIsNone(f.payld)
        self.assertIsNone(f.hops)
        self.assertIsNone(f.taddr)


    def test_available_payld_sz(self):
        f = HeymacFrame(HeymacFramePidType.CSMA,
                        saddr=b"\x10\x00",
                        hops=4,
                        taddr=b"\x11\x00")
        avail1 = f.available_payld_sz()
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x06\x10\x00\x04\x11\x00")

        # Add IEs to the frame
        ies=HeymacIeSequence(
            HeymacPIeFrag0(500, 21),
            HeymacPIeTerm())
        f.ies = ies
        avail2 = f.available_payld_sz()
        self.assertEqual(avail1, avail2 + len(ies))


if __name__ == '__main__':
    unittest.main()
