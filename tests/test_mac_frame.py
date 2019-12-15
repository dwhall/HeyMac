#!/usr/bin/env python3


import unittest

import heymac


class TestHeyMacFrame(unittest.TestCase):
    """Tests the heymac.HeyMacFrame packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """

    def test_mac(self,):
        # Pack
        f = heymac.HeyMacFrame()
        b = bytes(f)
        self.assertEqual(b, b"\xE8\x00")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertTrue(f.is_heymac())
        self.assertTrue(f.is_heymac_version_compatible())
        self.assertEqual(f.fctl_x, 0)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.fctl_m, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")
        self.assertEqual(f.hops, b"") # FIXME
        self.assertEqual(f.txaddr, b"")


    def test_csma(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.pid_protocol = heymac.HeyMacFrame.PID_PROTOCOL_HEYMAC
        f.pid_type = heymac.HeyMacFrame.PID_TYPE_CSMA
        b = bytes(f)
        self.assertEqual(b, b"\xE8\x00")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_x, 0)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.fctl_m, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")
        self.assertEqual(f.hops, b"")
        self.assertEqual(f.txaddr, b"")


    def test_min_payld(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.data = b"ABCD"
        b = bytes(f)
        self.assertEqual(b, b"\xE8\x00ABCD")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_x, 0)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.fctl_m, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"ABCD")
        self.assertEqual(f.hops, b"")
        self.assertEqual(f.txaddr, b"")


    def test_csma_ver(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.pid_protocol = heymac.HeyMacFrame.PID_PROTOCOL_HEYMAC
        f.pid_type = heymac.HeyMacFrame.PID_TYPE_CSMA
        f.pid_ver = 0 #heymac.HeyMacFrame.PID_VER_CSMA
        b = bytes(f)
        self.assertEqual(b, b"\xE8\x00")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.pid, 0xE8)
        self.assertEqual(f.fctl_x, 0)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.fctl_m, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"")
        self.assertEqual(f.hops, b"")
        self.assertEqual(f.txaddr, b"")


    def test_mac_saddr64b(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\xE8\x44\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_x, 0)
        self.assertEqual(f.fctl_l, 1)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 1)
        self.assertEqual(f.fctl_m, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.data, b"")
        self.assertEqual(f.hops, b"")
        self.assertEqual(f.txaddr, b"")


    def test_mac_len_saddr16b_beacon(self,):
        # Pack
        f = heymac.HeyMacFrame()
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
        self.assertEqual(b, b"\xE8\x04\x11\x12\x01\xf5\x02\x03\x04\x00\x00\x00\x2a\x00\x00\x00\x00\x00\x00\x00\x00")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_x, 0)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 1)
        self.assertEqual(f.fctl_m, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"\x11\x12")
        self.assertEqual(type(f.payld), heymac.mac_cmds.HeyMacCmdSbcn)
        self.assertEqual(f.payld.bcn_en, 1)
        self.assertEqual(f.payld.sf_order, 5)
        self.assertEqual(f.payld.eb_order, 7)
        self.assertEqual(f.payld.dscpln, 2)
        self.assertEqual(f.payld.caps, 3)
        self.assertEqual(f.payld.status, 4)
        self.assertEqual(f.payld.asn, 42)
        self.assertEqual(f.hops, b"")
        self.assertEqual(f.txaddr, b"")


    def test_mac_len_saddr64b(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.saddr = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        b = bytes(f)
        self.assertEqual(b, b"\xE8\x44\x01\x02\x03\x04\x05\x06\x07\x08")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_x, 0)
        self.assertEqual(f.fctl_l, 1)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 1)
        self.assertEqual(f.fctl_m, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertEqual(f.data, b"")
        self.assertEqual(f.hops, b"")
        self.assertEqual(f.txaddr, b"")


    def test_mac_len_saddr64b_daddr64b(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.daddr = b"\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8"
        f.saddr = b"\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8"
        f.data = b"hi"
        b = bytes(f)
        self.assertEqual(b, b"\xE8\x54\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8hi")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_x, 0)
        self.assertEqual(f.fctl_l, 1)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 1)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 1)
        self.assertEqual(f.fctl_m, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8")
        self.assertEqual(f.saddr, b"\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8")
        self.assertEqual(f.data, b"hi")
        self.assertEqual(f.hops, b"")
        self.assertEqual(f.txaddr, b"")


    def test_mac_len_saddr16b_daddr16b(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.daddr = b"\xd1\xd2"
        f.saddr = b"\xc1\xc2"
        f.data = b"hello world"
        b = bytes(f)
        self.assertEqual(b, b"\xE8\x14\xd1\xd2\xc1\xc2hello world")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_x, 0)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 1)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 1)
        self.assertEqual(f.fctl_m, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"\xd1\xd2")
        self.assertEqual(f.saddr, b"\xc1\xc2")
        self.assertEqual(f.data, b"hello world")
        self.assertEqual(f.hops, b"")
        self.assertEqual(f.txaddr, b"")


    def test_net_data(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.data = heymac.APv6Frame()
        b = bytes(f)
        self.assertEqual(b, b"\xE8\x00\xD7")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_x, 0)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.fctl_m, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(type(f.payld), heymac.APv6Frame)


    def test_pvs(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.data = b"6x7"
        b = bytes(f)
        self.assertEqual(b, b"\xE8\x006x7")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_x, 0)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_n, 0)
        self.assertEqual(f.fctl_d, 0)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.fctl_m, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.netid, b"")
        self.assertEqual(f.daddr, b"")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"6x7")
        self.assertEqual(f.hops, b"")
        self.assertEqual(f.txaddr, b"")


    def test_netid_daddr(self,):
        # Pack
        f = heymac.HeyMacFrame()
        f.netid = 0x80A5
        f.daddr = 0xd1d2
        f.data = b"data"
        b = bytes(f)
        self.assertEqual(b, b"\xE8\x30\x80\xa5\xd1\xd2data")
        # Unpack
        f = heymac.HeyMacFrame(b)
        self.assertEqual(f.fctl_x, 0)
        self.assertEqual(f.fctl_l, 0)
        self.assertEqual(f.fctl_n, 1)
        self.assertEqual(f.fctl_d, 1)
        self.assertEqual(f.fctl_i, 0)
        self.assertEqual(f.fctl_s, 0)
        self.assertEqual(f.fctl_m, 0)
        self.assertEqual(f.fctl_p, 0)
        self.assertEqual(f.netid, b"\x80\xA5")
        self.assertEqual(f.daddr, b"\xd1\xd2")
        self.assertEqual(f.saddr, b"")
        self.assertEqual(f.data, b"data")
        self.assertEqual(f.hops, b"")
        self.assertEqual(f.txaddr, b"")


if __name__ == '__main__':
    unittest.main()
