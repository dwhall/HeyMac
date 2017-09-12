import unittest

from HeyMac import *


class TestHeyMacFrame(unittest.TestCase):
    """Tests the HeyMacFrame packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """
    
    def test_min(self,):
        # Pack
        f = HeyMacFrame()
        f.omit_lencode = True
        b = bytes(f)
        self.assertEqual(b, b"\x00")
        # Unpack
        f = HeyMacFrame(b)
        self.assertEqual(f.fctl, 0)
        self.assertEqual(f.lencode, None)
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_min_lencode(self,):
        # Pack
        f = HeyMacFrame()
        b = bytes(f)
        self.assertEqual(b, b"\x20\x01")
        # Unpack
        f = HeyMacFrame(b)
        self.assertEqual(f.fctl, FCTL_TYPE_MIN | FCTL_LENCODE_BIT)
        self.assertEqual(f.lencode, 1)
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_min_saddr64b(self,):
        # Pack
        f = HeyMacFrame()
        f.omit_lencode = True
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\x04\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = HeyMacFrame(b)
        self.assertEqual(f.fctl, FCTL_TYPE_MIN | FCTL_SADDR_MODE_64BIT)
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_mac_verseq_saddr64b(self,):
        # Pack
        f = HeyMacFrame()
        f.omit_lencode = True
        f.fctl |= FCTL_TYPE_MAC
        f.seq = 1
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\x44\x11\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = HeyMacFrame(b)
        self.assertEqual(f.fctl, FCTL_TYPE_MAC | FCTL_SADDR_MODE_64BIT)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 1)
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_mac_len_verseq_saddr16b_beacon(self,):
        # Unpack
        b = b"h\r\x11\xb0\x0b\x01\x00\x00\x00\x02\x00\x00\x00\x00"
        f = HeyMacFrame()
        self.assertTrue(type(f.data), HeyMacCmdBeacon)
    
    def test_mac_len_verseq_saddr64b(self,):
        # Pack
        f = HeyMacFrame()
        f.fctl |= FCTL_TYPE_MAC
        f.seq = 2
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\x64\x0a\x12\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = HeyMacFrame(b)
        self.assertEqual(f.fctl, FCTL_TYPE_MAC | FCTL_LENCODE_BIT | FCTL_SADDR_MODE_64BIT)
        self.assertEqual(f.lencode, 10)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 2)
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"")

    def test_mac_len_verseq_saddr64b_daddr64b(self,):
        # Pack
        f = HeyMacFrame()
        f.fctl = FCTL_TYPE_MAC
        f.daddr = b"\xff\xff\xff\xff\xff\xff\xff\xff"
        f.saddr = b"\xab\xcd\xef\x01\x02\x03\x04\x05"
        f.data = b"hi"
        b = bytes(f)
        self.assertEqual(b, b"\x65\x14\x10\xff\xff\xff\xff\xff\xff\xff\xff\xab\xcd\xef\x01\x02\x03\x04\x05hi")
        # Unpack
        f = HeyMacFrame(b)
        self.assertEqual(f.fctl, FCTL_TYPE_MAC | FCTL_LENCODE_BIT | FCTL_SADDR_MODE_64BIT | FCTL_DADDR_MODE_64BIT)
        self.assertEqual(f.lencode, 20)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.saddr, b"\xab\xcd\xef\x01\x02\x03\x04\x05")
        self.assertEqual(f.daddr, b"\xff\xff\xff\xff\xff\xff\xff\xff")
        self.assertEqual(f.data, b"hi")

    def test_mac_len_verseq_saddr16b_daddr16b(self,):
        # Pack
        f = HeyMacFrame()
        f.fctl = FCTL_TYPE_MAC
        f.daddr = b"\xff\xff"
        f.saddr = b"\xab\xcd"
        f.data = b"hello world"
        b = bytes(f)
        self.assertEqual(b, b"\x6A\x11\x10\xff\xff\xab\xcdhello world")
        # Unpack
        f = HeyMacFrame(b)
        self.assertEqual(f.fctl, FCTL_TYPE_MAC | FCTL_LENCODE_BIT | FCTL_SADDR_MODE_16BIT | FCTL_DADDR_MODE_16BIT)
        self.assertEqual(f.lencode, 17)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.saddr, b"\xab\xcd")
        self.assertEqual(f.daddr, b"\xff\xff")
        self.assertEqual(f.data, b"hello world")

    def test_nlh_len_data(self,):
        # Pack
        f = HeyMacFrame()
        f.fctl |= FCTL_TYPE_NLH
        f.data = b"ipv6_hdr_compression"
        b = bytes(f)
        self.assertEqual(b, b"\xA0\x16\x10ipv6_hdr_compression")
        # Unpack
        f = HeyMacFrame(b)
        self.assertEqual(f.fctl, FCTL_TYPE_NLH | FCTL_LENCODE_BIT)
        self.assertEqual(f.lencode, 22)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"ipv6_hdr_compression")


    def test_nlh_len_data(self,):
        # Pack
        f = HeyMacFrame()
        f.fctl |= FCTL_TYPE_EXT
        f.exttype = b"\x2A"
        f.data = b"6x7"
        b = bytes(f)
        self.assertEqual(b, b"\xE0\x06\x10\x2A6x7")
        # Unpack
        f = HeyMacFrame(b)
        self.assertEqual(f.fctl, FCTL_TYPE_EXT | FCTL_LENCODE_BIT)
        self.assertEqual(f.lencode, 6)
        self.assertEqual(f.ver, 1)
        self.assertEqual(f.seq, 0)
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.data, b"6x7")


if __name__ == '__main__':
    unittest.main()
