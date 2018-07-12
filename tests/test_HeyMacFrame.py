#!/usr/bin/env python3


import unittest

import mac_cmds
import mac_frame


class TestHeyMacFrame(unittest.TestCase):
    """Tests the mac_frame.HeyMacFrame packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """

    def test_min(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl = mac_frame.FCTL_TYPE_MIN
        b = bytes(f)
        self.assertEqual(b, b"\x00")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MIN)
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.data, b"")

    def test_mac(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_MAC
        f.raddr = b"\x00\x00"
        b = bytes(f)
        self.assertEqual(b, b"\x40\x10\x00\x00")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.raddr, b"\x00\x00")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_net(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl = mac_frame.FCTL_TYPE_NET
        f.raddr = b"\x00\x00"
        b = bytes(f)
        self.assertEqual(b, b"\x80\x10\x00\x00")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_NET)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.raddr, b"\x00\x00")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_ext_using_fctl(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_EXT
        f.raddr = b"\x00\x00"
        b = bytes(f)
        self.assertEqual(b, b"\xC0\x10\x00\x00\x00")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_EXT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.exttype, 0)
        self.assertEqual(f.raddr, b"\x00\x00")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_ext_using_field(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.raddr = b"\x11\x11"
        f.exttype = b"\x00"
        b = bytes(f)
        self.assertEqual(b, b"\xC0\x10\x11\x11\x00")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_EXT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.exttype, 0)
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_min_payld(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl = mac_frame.FCTL_TYPE_MIN
        f.data = b"ABCD"
        b = bytes(f)
        self.assertEqual(b, b"\x00ABCD")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MIN)
        self.assertEqual(f.raddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"ABCD")

    def test_mac_verseq(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_MAC
        f.seq = 7
        f.raddr = b"\x00\x00"
        b = bytes(f)
        self.assertEqual(b, b"\x40\x17\x00\x00")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 7)
        self.assertEqual(f.raddr, b"\x00\x00")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_min_saddr64b(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl = mac_frame.FCTL_TYPE_MIN
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\x22\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MIN | mac_frame.FCTL_LONG_ADDR_EN | mac_frame.FCTL_SRC_ADDR_PRESENT)
        self.assertEqual(f.raddr, b"")
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_mac_verseq_saddr64b(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_MAC
        f.seq = 9
        f.raddr = b"\x21\x22\x23\x24\x25\x26\x27\x28"
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\x62\x19\x21\x22\x23\x24\x25\x26\x27\x28\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC | mac_frame.FCTL_LONG_ADDR_EN | mac_frame.FCTL_SRC_ADDR_PRESENT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 9)
        self.assertEqual(f.raddr, b"\x21\x22\x23\x24\x25\x26\x27\x28")
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_mac_len_verseq_saddr16b_beacon(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_MAC
        f.seq = 2
        f.raddr = b"\x11\x12"
        f.saddr = b"\x11\x12"
        bcn = mac_cmds.HeyMacCmdSbcn(
            bcn_en=1,
            sf_order=5,
            eb_order=10,
            dscpln=2,
            caps=3,
            status=4,
            asn=42,
        )
        f.data = bytes(bcn)
        b = bytes(f)
        self.assertEqual(b, b"\x42\x12\x11\x12\x11\x12\x01\xda\x02\x03\x04\x00\x00\x00\x2a\x00\x00\x00\x00\x00\x00\x00\x00")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC | mac_frame.FCTL_SRC_ADDR_PRESENT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 2)
        self.assertEqual(f.raddr, b"\x11\x12")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"\x11\x12")
        self.assertTrue(type(f.data), mac_cmds.HeyMacCmdSbcn)
        self.assertTrue(f.data.bcn_en, 1)
        self.assertTrue(f.data.sf_order, 5)
        self.assertTrue(f.data.eb_order, 10)
        self.assertTrue(f.data.dscpln, 2)
        self.assertTrue(f.data.caps, 3)
        self.assertTrue(f.data.status, 4)
        self.assertTrue(f.data.asn, 42)

    def test_mac_len_verseq_saddr64b(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_MAC
        f.seq = 2
        f.raddr = b"\x11\x11\x11\x11\x11\x11\x11\x11"
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\x62\x12\x11\x11\x11\x11\x11\x11\x11\x11\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC | mac_frame.FCTL_LONG_ADDR_EN | mac_frame.FCTL_SRC_ADDR_PRESENT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 2)
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_mac_len_verseq_saddr64b_daddr64b(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl = mac_frame.FCTL_TYPE_MAC
        f.raddr = b"\x11\x11\x11\x11\x11\x11\x11\x11"
        f.daddr = b"\xff\xff\xff\xff\xff\xff\xff\xff"
        f.saddr = b"\xab\xcd\xef\x01\x02\x03\x04\x05"
        f.data = b"hi"
        b = bytes(f)
        self.assertEqual(b, b"\x6A\x10\x11\x11\x11\x11\x11\x11\x11\x11\xff\xff\xff\xff\xff\xff\xff\xff\xab\xcd\xef\x01\x02\x03\x04\x05hi")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC | mac_frame.FCTL_LONG_ADDR_EN | mac_frame.FCTL_SRC_ADDR_PRESENT | mac_frame.FCTL_DST_ADDR_PRESENT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.saddr, b"\xab\xcd\xef\x01\x02\x03\x04\x05")
        self.assertEqual(f.daddr, b"\xff\xff\xff\xff\xff\xff\xff\xff")
        self.assertEqual(f.data, b"hi")

    def test_mac_len_verseq_saddr16b_daddr16b(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl = mac_frame.FCTL_TYPE_MAC
        f.raddr = b"\x11\x11"
        f.daddr = b"\xff\xff"
        f.saddr = b"\xab\xcd"
        f.data = b"hello world"
        b = bytes(f)
        self.assertEqual(b, b"\x4A\x10\x11\x11\xff\xff\xab\xcdhello world")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC | mac_frame.FCTL_SRC_ADDR_PRESENT | mac_frame.FCTL_DST_ADDR_PRESENT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.saddr, b"\xab\xcd")
        self.assertEqual(f.daddr, b"\xff\xff")
        self.assertEqual(f.data, b"hello world")

    def test_net_data(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl = mac_frame.FCTL_TYPE_NET
        f.raddr = b"\x11\x11"
        f.data = b"ipv6_hdr_compression"
        b = bytes(f)
        self.assertEqual(b, b"\x80\x10\x11\x11ipv6_hdr_compression")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_NET )
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.raddr, b"\x11\x11")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"ipv6_hdr_compression")


    def test_ext_data(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_EXT
        f.raddr = b"\x11\x11"
        f.exttype = b"\x2A"
        f.data = b"6x7"
        b = bytes(f)
        self.assertEqual(b, b"\xC0\x10\x11\x11\x2A6x7")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_EXT )
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.raddr, b"\x11\x11")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"6x7")


if __name__ == '__main__':
    unittest.main()
