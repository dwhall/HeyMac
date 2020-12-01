#!/usr/bin/env python3


import unittest

from lnk_heymac import HeymacFrame


class TestHeyMacFrame(unittest.TestCase):
    """Tests the HeymacFrame building and serializing.
    """

    def test_mac(self,):
        # Build and serialize
        f = HeymacFrame(
                HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
                0)
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x00")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertTrue(f.is_heymac())
        self.assertEqual(f.get_field(HeymacFrame.FLD_FCTL), 0)
        self.assertIsNone(f.get_field(HeymacFrame.FLD_NETID))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_DADDR))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_SADDR))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_PAYLD))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_HOPS))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_TADDR))


    def test_not_mac(self,):
        b = b"\x00\x00"
        # Parse and test
        # expect that parser raises exception due to invalid frame header
        self.assertRaises(AssertionError, HeymacFrame.parse, b)


    def test_csma(self,):
        # Build and serialize
        f = HeymacFrame(
                HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
                0)
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x00")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.get_field(HeymacFrame.FLD_FCTL), 0x00)
        self.assertIsNone(f.get_field(HeymacFrame.FLD_NETID))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_DADDR))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_SADDR))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_PAYLD))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_HOPS))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_TADDR))


    def test_min_payld(self,):
        # Build and serialize
        f = HeymacFrame(
                HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
                0)
        f.set_field(HeymacFrame.FLD_PAYLD, b"ABCD")
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x00ABCD")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.get_field(HeymacFrame.FLD_FCTL), 0)
        self.assertIsNone(f.get_field(HeymacFrame.FLD_NETID))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_DADDR))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_SADDR))
        self.assertEqual(f.get_field(HeymacFrame.FLD_PAYLD), b"ABCD")
        self.assertIsNone(f.get_field(HeymacFrame.FLD_HOPS))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_TADDR))


    def test_saddr64b(self,):
        # Build and serialize
        f = HeymacFrame(
                HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
                HeymacFrame.FCTL_L | HeymacFrame.FCTL_S)
        f.set_field(HeymacFrame.FLD_SADDR, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x44\x01\x02\x03\x04\x05\x06\x07\x08")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.get_field(HeymacFrame.FLD_FCTL), 0x44)
        self.assertIsNone(f.get_field(HeymacFrame.FLD_NETID))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_DADDR))
        self.assertEqual(f.get_field(HeymacFrame.FLD_SADDR), b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertIsNone(f.get_field(HeymacFrame.FLD_PAYLD))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_HOPS))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_TADDR))


    """
    def test_len_saddr16b_beacon(self,):
        # Build and serialize
        f = HeymacFrame(
                HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
                HeymacFrame.FCTL_S)
        f.set_field(HeymacFrame.FLD_SADDR, b"\x11\x12")
        bcn = heymac.mac_cmds.HeyMacCmdSbcn(
            bcn_en=1,
            sf_order=5,
            eb_order=7,
            dscpln=2,
            caps=3,
            status=4,
            asn=42,
        )
        f.get_field(HeymacFrame.FLD_PAYLD) = bytes(bcn)
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x04\x11\x12\x81\xf5\x02\x03\x04\x00\x00\x00\x2a\x00\x00\x00\x00\x00\x00\x00\x00")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.get_field(HeymacFrame.FLD_FCTL) & HeymacFrame.FCTL_X, 0x04)
        self.assertIsNone(f.get_field(HeymacFrame.FLD_NETID))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_DADDR))
        self.assertEqual(f.get_field(HeymacFrame.FLD_SADDR), b"\x11\x12")
        self.assertEqual(type(f.payld), heymac.mac_cmds.HeyMacCmdSbcn)
        self.assertEqual(f.payld.bcn_en, 1)
        self.assertEqual(f.payld.sf_order, 5)
        self.assertEqual(f.payld.eb_order, 7)
        self.assertEqual(f.payld.dscpln, 2)
        self.assertEqual(f.payld.caps, 3)
        self.assertEqual(f.payld.status, 4)
        self.assertEqual(f.payld.asn, 42)
        self.assertIsNone(f.get_field(HeymacFrame.FLD_HOPS))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_TADDR))
    """

    def test_saddr64b_daddr64b(self,):
        # Build and serialize
        f = HeymacFrame(
                HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
                HeymacFrame.FCTL_L | HeymacFrame.FCTL_D | HeymacFrame.FCTL_S)
        f.set_field(HeymacFrame.FLD_DADDR, b"\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8")
        f.set_field(HeymacFrame.FLD_SADDR, b"\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8")
        f.set_field(HeymacFrame.FLD_PAYLD, b"hi")
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x54\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8hi")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.get_field(HeymacFrame.FLD_FCTL), 0x54)
        self.assertIsNone(f.get_field(HeymacFrame.FLD_NETID))
        self.assertEqual(f.get_field(HeymacFrame.FLD_DADDR), b"\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8")
        self.assertEqual(f.get_field(HeymacFrame.FLD_SADDR), b"\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8")
        self.assertEqual(f.get_field(HeymacFrame.FLD_PAYLD), b"hi")
        self.assertIsNone(f.get_field(HeymacFrame.FLD_HOPS))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_TADDR))


    def test_saddr16b_daddr16b(self,):
        # Build and serialize
        f = HeymacFrame(
                HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
                HeymacFrame.FCTL_S | HeymacFrame.FCTL_D)
        f.set_field(HeymacFrame.FLD_DADDR, b"\xd1\xd2")
        f.set_field(HeymacFrame.FLD_SADDR, b"\xc1\xc2")
        f.set_field(HeymacFrame.FLD_PAYLD, b"hello world")
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x14\xd1\xd2\xc1\xc2hello world")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.get_field(HeymacFrame.FLD_FCTL), 0x14)
        self.assertIsNone(f.get_field(HeymacFrame.FLD_NETID))
        self.assertEqual(f.get_field(HeymacFrame.FLD_DADDR), b"\xd1\xd2")
        self.assertEqual(f.get_field(HeymacFrame.FLD_SADDR), b"\xc1\xc2")
        self.assertEqual(f.get_field(HeymacFrame.FLD_PAYLD), b"hello world")
        self.assertIsNone(f.get_field(HeymacFrame.FLD_HOPS))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_TADDR))


    """
    def test_net_data(self,):
        # Build and serialize
        f = HeymacFrame(
                HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
                0)
        f.set_field(HeymacFrame.FLD_PAYLD, heymac.APv6Frame())
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x00\xD7")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.get_field(HeymacFrame.FLD_FCTL), 0)
        self.assertIsNone(f.get_field(HeymacFrame.FLD_NETID))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_DADDR))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_SADDR))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_HOPS))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_TADDR))
        self.assertEqual(type(f.payld), heymac.APv6Frame)
    """


    def test_netid_daddr(self,):
        # Build and serialize
        f = HeymacFrame(
                HeymacFrame.PID_IDENT_HEYMAC | HeymacFrame.PID_TYPE_CSMA,
                HeymacFrame.FCTL_N | HeymacFrame.FCTL_D)
        f.set_field(HeymacFrame.FLD_NETID, b"\x80\xA5")
        f.set_field(HeymacFrame.FLD_DADDR, b"\xd1\xd2")
        f.set_field(HeymacFrame.FLD_PAYLD, b"data")
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x30\x80\xa5\xd1\xd2data")
        # Parse and test
        f = HeymacFrame.parse(b)
        self.assertEqual(f.get_field(HeymacFrame.FLD_FCTL), 0x30)
        self.assertEqual(f.get_field(HeymacFrame.FLD_NETID), b"\x80\xA5")
        self.assertEqual(f.get_field(HeymacFrame.FLD_DADDR), b"\xd1\xd2")
        self.assertIsNone(f.get_field(HeymacFrame.FLD_SADDR))
        self.assertEqual(f.get_field(HeymacFrame.FLD_PAYLD), b"data")
        self.assertIsNone(f.get_field(HeymacFrame.FLD_HOPS))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_TADDR))


    """
    def test_csma_ver0(self,):
        # Build and serialize
        f = HeymacFrameCsmaV0()
        f.pid_protocol = HeymacFrame.PID_PROTOCOL_HEYMAC
        f.pid_type = HeymacFrame.PID_TYPE_CSMA
        f.pid_ver = 0 #HeymacFrame.PID_VER_CSMA
        b = bytes(f)
        self.assertEqual(b, b"\xE4\x00")
        # Parse and test
        f = HeymacFrameCsmaV0(b)
        self.assertEqual(f.pid, 0xE4)
        self.assertEqual(f.get_field(HeymacFrame.FLD_FCTL), 0x00)
        self.assertIsNone(f.get_field(HeymacFrame.FLD_NETID))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_DADDR))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_SADDR))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_PAYLD))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_HOPS))
        self.assertIsNone(f.get_field(HeymacFrame.FLD_TADDR))
    """

if __name__ == '__main__':
    unittest.main()
