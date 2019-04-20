#!/usr/bin/env python3


import unittest

import heymac


class TestHeyMacFrame(unittest.TestCase):
    """Tests the heymac.HeyMacFrame packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """

    def test_min(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MIN
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x00")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MIN)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_mac(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MAC
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x40")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MAC)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_net(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_NET
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x80")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_NET)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_ext_using_fctl(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_EXT
        b = bytes(f)
        self.assertEqual(b, b"\xE2\xC0\x00")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_EXT)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, 0)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_ext_using_field(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.exttype = b"\x05"
        b = bytes(f)
        self.assertEqual(b, b"\xE2\xC0\x05")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_EXT)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, 5)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_min_payld(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MIN
        f.data = b"ABCD"
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x00ABCD")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MIN)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"ABCD")

    def test_mac_verseq(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MAC
        f.seq = 7
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x40")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MAC)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_min_saddr64b(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MIN
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x21\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MIN)
        self.assertEqual(f.fctl_l, 1)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 1)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.data, b"")

    def test_mac_verseq_saddr64b(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MAC
        f.seq = 9
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x61\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MAC)
        self.assertEqual(f.fctl_l, 1)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 1)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.data, b"")

    def test_mac_len_verseq_saddr16b_beacon(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MAC
        f.seq = 2
        f.saddr = b"\x11\x12"
        bcn = heymac.mac_cmds.HeyMacCmdSbcn(
            bcn_en=1,
            sf_order=5,
            eb_order=7,
            dscpln=2,
            caps=3,
            status=4,
            asn=42,
        )
        f.data = bytes(bcn)
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x41\x11\x12\x01\xf5\x02\x03\x04\x00\x00\x00\x2a\x00\x00\x00\x00\x00\x00\x00\x00")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MAC)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 1)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"\x11\x12")
        self.assertEqual(type(f.data), heymac.mac_cmds.HeyMacCmdSbcn)
        self.assertEqual(f.data.bcn_en, 1)
        self.assertEqual(f.data.sf_order, 5)
        self.assertEqual(f.data.eb_order, 7)
        self.assertEqual(f.data.dscpln, 2)
        self.assertEqual(f.data.caps, 3)
        self.assertEqual(f.data.status, 4)
        self.assertEqual(f.data.asn, 42)

    def test_mac_len_verseq_saddr64b(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MAC
        f.seq = 2
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x61\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MAC)
        self.assertEqual(f.fctl_l, 1)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 1)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.data, b"")

    def test_mac_len_verseq_saddr64b_daddr64b(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MAC
        f.daddr = b"\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8"
        f.saddr = b"\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8"
        f.data = b"hi"
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x65\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8hi")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MAC)
        self.assertEqual(f.fctl_l, 1)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 1)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 1)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8")
        self.assertEqual(f.saddr, b"\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8")
        self.assertEqual(f.data, b"hi")

    def test_mac_len_verseq_saddr16b_daddr16b(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MAC
        f.daddr = b"\xd1\xd2"
        f.saddr = b"\xc1\xc2"
        f.data = b"hello world"
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x45\xd1\xd2\xc1\xc2hello world")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MAC)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 1)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 1)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"\xd1\xd2")
        self.assertEqual(f.saddr, b"\xc1\xc2")
        self.assertEqual(f.data, b"hello world")

    def test_net_data(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_NET
        f.data = heymac.APv6Frame()
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x80\xD7")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_NET)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(type(f.data), heymac.APv6Frame)


    def test_ext_data(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_EXT
        f.exttype = b"\x2A"
        f.data = b"6x7"
        b = bytes(f)
        self.assertEqual(b, b"\xE2\xC0\x2A6x7")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_EXT)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, 42)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"6x7")


    def test_pvs(self,):
        """Tests a frame with _pvs field present
        to ensure fields are in proper order
        """
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MAC
        f.seq = 9
        f.data = b"6x7"
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x406x7")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MAC)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"6x7")


    def test_exttype_netid(self,):
        """Tests a frame with exttype and NetID fields present
        to ensure fields are in proper order
        """
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MAC
        f.exttype = 3
        f.netid = 0x80A5
        f.data = b"data"
        b = bytes(f)
        self.assertEqual(b, b"\xE2\xC8\x03\x80\xa5data")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_EXT)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 1)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, 3)
        self.assertEqual(f.netid, b"\x80\xA5")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"data")


    def test_netid_daddr(self,):
        """Tests a frame with NetID and Dest addr fields present
        to ensure fields are in proper order
        """
        # Pack
        f = heymac.HeyMacFrame()
        f.fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MAC
        f.netid = 0x80A5
        f.daddr = 0xd1d2
        f.data = b"data"
        b = bytes(f)
        self.assertEqual(b, b"\xE2\x4C\x80\xa5\xd1\xd2data")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MAC)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 1)
        self.assertEqual(f.fctl_d, 1)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"\x80\xA5")
        self.assertEqual(f.daddr, b"\xd1\xd2")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"data")


class TestHeyMacFloodFrame(unittest.TestCase):
    def test_min(self,):
        f = heymac.HeyMacFloodFrame()
        f.fctl_type = heymac.HeyMacFloodFrame.FCTL_TYPE_MIN
        b = bytes(f)
        self.assertEqual(b, b"\xF2\x00")
        # Unpack
        f = heymac.HeyMacFloodFrame(b)
        self.assertEqual(f.fctl_type, heymac.HeyMacFloodFrame.FCTL_TYPE_MIN)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.exttype, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")


if __name__ == '__main__':
    unittest.main()
