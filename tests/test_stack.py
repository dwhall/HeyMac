#!/usr/bin/env python3


import unittest

import heymac


class TestAll(unittest.TestCase):
    """Tests packing and unpacking of HeyMac, APv6 and UDP layers together.
    Each test function should test pack and unpack of the same data.
    """

    def test_mac_min(self,):
        # Pack
        fmac = heymac.HeyMacFrame(fctl_type = heymac.HeyMacFrame.FCTL_TYPE_MIN)
        b = bytes(fmac)
        self.assertEqual(b, b"\xe2\x00")
        # Unpack
        fmac = heymac.HeyMacFrame(b)
        self.assertEqual(fmac.pv_pid, fmac.PV_PID_HEYMAC)
        self.assertEqual(fmac.pv_ver, fmac.PV_VER_HEYMAC2)
        self.assertEqual(fmac.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_MIN)
        self.assertEqual(fmac.fctl_l, 0)
        self.assertEqual(fmac.fctl_p, 0)
        self.assertEqual(fmac.fctl_n, 0)
        self.assertEqual(fmac.fctl_d, 0)
        self.assertEqual(fmac.fctl_i, 0)
        self.assertEqual(fmac.fctl_s, 0)
        self.assertEqual(fmac.exttype, b"")
        self.assertEqual(fmac.netid, b"")
        self.assertEqual(fmac.daddr, b"")
        self.assertEqual(fmac.saddr, b"")
        self.assertEqual(fmac.data, b"")

    def test_mac_net_min(self,):
        # Pack
        fmac = heymac.HeyMacFrame(fctl_type=heymac.HeyMacFrame.FCTL_TYPE_NET)
        fnet = heymac.APv6Frame()
        fmac.data = fnet
        b = bytes(fmac)
        self.assertEqual(b, b"\xe2\x80\xD7")
        # Unpack HeyMacFrame
        fmac = heymac.HeyMacFrame(b)
        self.assertEqual(fmac.pv_pid, fmac.PV_PID_HEYMAC)
        self.assertEqual(fmac.pv_ver, fmac.PV_VER_HEYMAC2)
        self.assertEqual(fmac.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_NET)
        self.assertEqual(fmac.fctl_l, 0)
        self.assertEqual(fmac.fctl_p, 0)
        self.assertEqual(fmac.fctl_n, 0)
        self.assertEqual(fmac.fctl_d, 0)
        self.assertEqual(fmac.fctl_i, 0)
        self.assertEqual(fmac.fctl_s, 0)
        self.assertEqual(fmac.exttype, b"")
        self.assertEqual(fmac.netid, b"")
        self.assertEqual(fmac.daddr, b"")
        self.assertEqual(fmac.saddr, b"")
        self.assertTrue(len(fmac.data) > 0)
        # Unpack APv6Frame
        fnet = fmac.data
        self.assertEqual(type(fnet), heymac.APv6Frame)
        self.assertEqual(fnet.iphc_prefix, 6)
        self.assertEqual(fnet.iphc_nhc, 1)
        self.assertEqual(fnet.iphc_hlim, 1)
        self.assertEqual(fnet.iphc_sam, 1)
        self.assertEqual(fnet.iphc_dam, 1)
        self.assertEqual(fnet.hops, 0x01)
        self.assertEqual(fnet.src, b"")
        self.assertEqual(fnet.dst, b"")

    def test_mac_net_udp_min(self,):
        # Pack
        fmac = heymac.HeyMacFrame(fctl_type=heymac.HeyMacFrame.FCTL_TYPE_NET)
        fnet = heymac.APv6Frame()
        fudp = heymac.APv6Udp(src_port=0xF0B0, dst_port=0xF0B0)
        fmac.data = fnet
        fnet.data = fudp
        b = bytes(fmac)
        self.assertEqual(b, b"\xe2\x80\xD7\xF7\x00")
        # Unpack HeyMacFrame
        fmac = heymac.HeyMacFrame(b)
        self.assertEqual(fmac.pv_pid, fmac.PV_PID_HEYMAC)
        self.assertEqual(fmac.pv_ver, fmac.PV_VER_HEYMAC2)
        self.assertEqual(fmac.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_NET)
        self.assertEqual(fmac.fctl_l, 0)
        self.assertEqual(fmac.fctl_p, 0)
        self.assertEqual(fmac.fctl_n, 0)
        self.assertEqual(fmac.fctl_d, 0)
        self.assertEqual(fmac.fctl_i, 0)
        self.assertEqual(fmac.fctl_s, 0)
        self.assertEqual(fmac.exttype, b"")
        self.assertEqual(fmac.netid, b"")
        self.assertEqual(fmac.daddr, b"")
        self.assertEqual(fmac.saddr, b"")
        self.assertTrue(len(fmac.data) > 0)
        # Unpack APv6Frame
        fnet = fmac.data
        self.assertEqual(type(fnet), heymac.APv6Frame)
        self.assertEqual(fnet.iphc_prefix, 6)
        self.assertEqual(fnet.iphc_nhc, 1)
        self.assertEqual(fnet.iphc_hlim, 1)
        self.assertEqual(fnet.iphc_sam, 1)
        self.assertEqual(fnet.iphc_dam, 1)
        self.assertEqual(fnet.hops, 1)
        self.assertEqual(fnet.src, b"")
        self.assertEqual(fnet.dst, b"")
        # Unpack UDP
        fudp = fnet.data
        self.assertEqual(type(fudp), heymac.APv6Udp)
        self.assertEqual(fudp.hdr_type, 0b11110)
        self.assertEqual(fudp.hdr_co, 1)
        self.assertEqual(fudp.hdr_ports, 0b11)
        self.assertEqual(fudp.chksum, b"")
        self.assertEqual(fudp.src_port, 0xF0B0)
        self.assertEqual(fudp.dst_port, 0xF0B0)


    def test_mac_net_udp_to_root(self,):
        # Pack
        fmac = heymac.HeyMacFrame(
            fctl_type=heymac.HeyMacFrame.FCTL_TYPE_NET,
            pend=0,
            seq=2,
            saddr=b"\x35\x16"
            )
        fnet = heymac.APv6Frame()
        fudp = heymac.APv6Udp(
            src_port=0xF0B6,
            dst_port=0xF0B0,
            data=b"UdpData"
        )
        fmac.data = fnet
        fnet.data = fudp
        b = bytes(fmac)
        self.assertEqual(b, b"\xe2\x81\x35\x16\xD7\xF7\x60UdpData")
        # Unpack HeyMacFrame
        fmac = heymac.HeyMacFrame(b)
        self.assertEqual(fmac.pv_pid, fmac.PV_PID_HEYMAC)
        self.assertEqual(fmac.pv_ver, fmac.PV_VER_HEYMAC2)
        self.assertEqual(fmac.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_NET)
        self.assertEqual(fmac.fctl_l, 0)
        self.assertEqual(fmac.fctl_p, 0)
        self.assertEqual(fmac.fctl_n, 0)
        self.assertEqual(fmac.fctl_d, 0)
        self.assertEqual(fmac.fctl_i, 0)
        self.assertEqual(fmac.fctl_s, 1)
        self.assertEqual(fmac.exttype, b"")
        self.assertEqual(fmac.netid, b"")
        self.assertEqual(fmac.daddr, b"")
        self.assertEqual(fmac.saddr, b"\x35\x16")
        self.assertTrue(len(fmac.data) > 0)
        # Unpack APv6Frame
        fnet = fmac.data
        self.assertEqual(type(fnet), heymac.APv6Frame)
        self.assertEqual(fnet.iphc_prefix, 6)
        self.assertEqual(fnet.iphc_nhc, 1)
        self.assertEqual(fnet.iphc_hlim, 1)
        self.assertEqual(fnet.iphc_sam, 1)
        self.assertEqual(fnet.iphc_dam, 1)
        self.assertEqual(fnet.hops, 1)
        self.assertEqual(fnet.src, b"")
        self.assertEqual(fnet.dst, b"")
        # Unpack UDP
        fudp = fnet.data
        self.assertEqual(type(fudp), heymac.APv6Udp)
        self.assertEqual(fudp.hdr_type, 0b11110)
        self.assertEqual(fudp.hdr_co, 1)
        self.assertEqual(fudp.hdr_ports, 0b11)
        self.assertEqual(fudp.chksum, b"")
        self.assertEqual(fudp.src_port, 0xF0B6)
        self.assertEqual(fudp.dst_port, 0xF0B0)
        self.assertEqual(fudp.data, b"UdpData")


    def test_mac_net_udp_to_node(self,):
        # Pack
        fmac = heymac.HeyMacFrame(
            fctl_type=heymac.HeyMacFrame.FCTL_TYPE_NET,
            pend=0,
            seq=4,
            saddr=b"\x35\x16",
            daddr=b"\x83\x11"
            )
        fnet = heymac.APv6Frame()
        fudp = heymac.APv6Udp(
            src_port=0xF0BA,
            dst_port=0xF0BF,
            data=b"nodedata"
        )
        fmac.data = fnet
        fnet.data = fudp
        b = bytes(fmac)
        self.assertEqual(b, b"\xe2\x85\x83\x11\x35\x16\xD7\xF7\xAFnodedata")
        # Unpack HeyMacFrame
        fmac = heymac.HeyMacFrame(b)
        self.assertEqual(fmac.pv_pid, fmac.PV_PID_HEYMAC)
        self.assertEqual(fmac.pv_ver, fmac.PV_VER_HEYMAC2)
        self.assertEqual(fmac.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_NET)
        self.assertEqual(fmac.fctl_l, 0)
        self.assertEqual(fmac.fctl_p, 0)
        self.assertEqual(fmac.fctl_n, 0)
        self.assertEqual(fmac.fctl_d, 1)
        self.assertEqual(fmac.fctl_i, 0)
        self.assertEqual(fmac.fctl_s, 1)
        self.assertEqual(fmac.exttype, b"")
        self.assertEqual(fmac.netid, b"")
        self.assertEqual(fmac.daddr, b"\x83\x11")
        self.assertEqual(fmac.saddr, b"\x35\x16")
        self.assertTrue(len(fmac.data) > 0)
        # Unpack APv6Frame
        fnet = fmac.data
        self.assertEqual(type(fnet), heymac.APv6Frame)
        self.assertEqual(fnet.iphc_prefix, 6)
        self.assertEqual(fnet.iphc_nhc, 1)
        self.assertEqual(fnet.iphc_hlim, 1)
        self.assertEqual(fnet.iphc_sam, 1)
        self.assertEqual(fnet.iphc_dam, 1)
        self.assertEqual(fnet.hops, 1)
        self.assertEqual(fnet.src, b"")
        self.assertEqual(fnet.dst, b"")
        # Unpack UDP
        fudp = fnet.data
        self.assertEqual(type(fudp), heymac.APv6Udp)
        self.assertEqual(fudp.hdr_type, 0b11110)
        self.assertEqual(fudp.hdr_co, 1)
        self.assertEqual(fudp.hdr_ports, 0b11)
        self.assertEqual(fudp.chksum, b"")
        self.assertEqual(fudp.src_port, 0xF0BA)
        self.assertEqual(fudp.dst_port, 0xF0BF)
        self.assertEqual(fudp.data, b"nodedata")


    def test_mac_net_udp_to_google(self,):
        # Pack
        fmac = heymac.HeyMacFrame(
            fctl_type=heymac.HeyMacFrame.FCTL_TYPE_NET,
            pend=0,
            seq=8,
            saddr=b"\x35\x16",
            )
        google_ipv6_addr = b"\x20\x01\x48\x60\x48\x60\x00\x00\x00\x00\x00\x00\x00\x00\x88\x88"
        fnet = heymac.APv6Frame(
            dst=google_ipv6_addr,
        )
        fudp = heymac.APv6Udp(
            src_port=0xF0B0,
            dst_port=53,
            data=b"DnsRequest"
        )
        fmac.data = fnet
        fnet.data = fudp
        b = bytes(fmac)
        self.assertEqual(b, b"\xe2\x81\x35\x16\xD6" + google_ipv6_addr + b"\xF6\xB0\x00\x35DnsRequest")
        # Unpack HeyMacFrame
        fmac = heymac.HeyMacFrame(b)
        self.assertEqual(fmac.pv_pid, fmac.PV_PID_HEYMAC)
        self.assertEqual(fmac.pv_ver, fmac.PV_VER_HEYMAC2)
        self.assertEqual(fmac.fctl_type, heymac.HeyMacFrame.FCTL_TYPE_NET)
        self.assertEqual(fmac.fctl_l, 0)
        self.assertEqual(fmac.fctl_p, 0)
        self.assertEqual(fmac.fctl_n, 0)
        self.assertEqual(fmac.fctl_d, 0)
        self.assertEqual(fmac.fctl_i, 0)
        self.assertEqual(fmac.fctl_s, 1)
        self.assertEqual(fmac.exttype, b"")
        self.assertEqual(fmac.netid, b"")
        self.assertEqual(fmac.daddr, b"")
        self.assertEqual(fmac.saddr, b"\x35\x16")
        self.assertTrue(len(fmac.data) > 0)
        # Unpack APv6Frame
        fnet = fmac.data
        self.assertEqual(type(fnet), heymac.APv6Frame)
        self.assertEqual(fnet.iphc_prefix, 6)
        self.assertEqual(fnet.iphc_nhc, 1)
        self.assertEqual(fnet.iphc_hlim, 1)
        self.assertEqual(fnet.iphc_sam, 1)
        self.assertEqual(fnet.iphc_dam, 0)
        self.assertEqual(fnet.hops, 1)
        self.assertEqual(fnet.src, b"")
        self.assertEqual(fnet.dst, google_ipv6_addr)
        # Unpack UDP
        fudp = fnet.data
        self.assertEqual(type(fudp), heymac.APv6Udp)
        self.assertEqual(fudp.hdr_type, 0b11110)
        self.assertEqual(fudp.hdr_co, 1)
        self.assertEqual(fudp.hdr_ports, 0b10)
        self.assertEqual(fudp.chksum, b"")
        self.assertEqual(fudp.src_port, 0xF0B0)
        self.assertEqual(fudp.dst_port, 53)
        self.assertEqual(fudp.data, b"DnsRequest")

 
if __name__ == "__main__":
    unittest.main()
