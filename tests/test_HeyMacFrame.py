#!/usr/bin/env python3


import unittest

import mac_frame, mac_cmds


class TestHeyMacFrame(unittest.TestCase):
    """Tests the mac_frame.HeyMacFrame packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """

    def test_min(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
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
        b = bytes(f)
        self.assertEqual(b, b"\x40\x10")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_nlh(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_NLH
        b = bytes(f)
        self.assertEqual(b, b"\x80\x10")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_NLH)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_ext_using_fctl(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_EXT
        b = bytes(f)
        self.assertEqual(b, b"\xC0\x10\x00")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_EXT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.exttype, 0)
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")

    def test_ext_using_field(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.exttype = b"\x00" # FIXME: doing this MUST set fctl's FCTL_TYPE_EXT flag
        b = bytes(f)
        self.assertEqual(b, b"\xC0\x10\x00")
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
        f.data = b"ABCD"
        b = bytes(f)
        self.assertEqual(b, b"\x00ABCD")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MIN)
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"ABCD")

    def test_mac_verseq(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_MAC
        f.seq = 7
        b = bytes(f)
        self.assertEqual(b, b"\x40\x17")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 7)
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_min_saddr64b(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\x0A\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MIN | mac_frame.FCTL_EXT_ADDR_EN | mac_frame.FCTL_SRC_ADDR_PRESENT)
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_mac_verseq_saddr64b(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_MAC
        f.seq = 9
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\x4A\x19\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC | mac_frame.FCTL_EXT_ADDR_EN | mac_frame.FCTL_SRC_ADDR_PRESENT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 9)
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_mac_len_verseq_saddr16b_beacon(self,):
        # Unpack
        b = b"h\r\x11\xb0\x0b\x01\x00\x00\x00\x02\x00\x00\x00\x00"
        f = mac_frame.HeyMacFrame()
        self.assertTrue(type(f.data), mac_cmds.CmdPktSmallBcn)

    def test_mac_len_verseq_saddr64b(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_MAC
        f.seq = 2
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\x4A\x12\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC | mac_frame.FCTL_EXT_ADDR_EN | mac_frame.FCTL_SRC_ADDR_PRESENT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 2)
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_mac_len_verseq_saddr64b_daddr64b(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl = mac_frame.FCTL_TYPE_MAC
        f.daddr = b"\xff\xff\xff\xff\xff\xff\xff\xff"
        f.saddr = b"\xab\xcd\xef\x01\x02\x03\x04\x05"
        f.data = b"hi"
        b = bytes(f)
        self.assertEqual(b, b"\x4E\x10\xff\xff\xff\xff\xff\xff\xff\xff\xab\xcd\xef\x01\x02\x03\x04\x05hi")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC | mac_frame.FCTL_EXT_ADDR_EN | mac_frame.FCTL_SRC_ADDR_PRESENT | mac_frame.FCTL_DST_ADDR_PRESENT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.saddr, b"\xab\xcd\xef\x01\x02\x03\x04\x05")
        self.assertEqual(f.daddr, b"\xff\xff\xff\xff\xff\xff\xff\xff")
        self.assertEqual(f.data, b"hi")

    def test_mac_len_verseq_saddr16b_daddr16b(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl = mac_frame.FCTL_TYPE_MAC
        f.daddr = b"\xff\xff"
        f.saddr = b"\xab\xcd"
        f.data = b"hello world"
        b = bytes(f)
        self.assertEqual(b, b"\x46\x10\xff\xff\xab\xcdhello world")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_MAC | mac_frame.FCTL_SRC_ADDR_PRESENT | mac_frame.FCTL_DST_ADDR_PRESENT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.saddr, b"\xab\xcd")
        self.assertEqual(f.daddr, b"\xff\xff")
        self.assertEqual(f.data, b"hello world")

    def test_nlh_len_data(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_NLH
        f.data = b"ipv6_hdr_compression"
        b = bytes(f)
        self.assertEqual(b, b"\xA0\x16\x10ipv6_hdr_compression")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_NLH )
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"ipv6_hdr_compression")


    def test_nlh_len_data(self,):
        # Pack
        f = mac_frame.HeyMacFrame()
        f.fctl |= mac_frame.FCTL_TYPE_EXT # FIXME: this is required for bytes() to have nonzero Fctl field and process VerSeq properly
        f.exttype = b"\x2A"
        f.data = b"6x7"
        b = bytes(f)
        self.assertEqual(b, b"\xC0\x10\x2A6x7")
        # Unpack
        f = mac_frame.HeyMacFrame(b)
        self.assertEqual(f.fctl, mac_frame.FCTL_TYPE_EXT )
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"6x7")


if __name__ == '__main__':
    unittest.main()
