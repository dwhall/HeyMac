#!/usr/bin/env python3


import unittest

from heymac.lnk import *
from heymac.net import APv6Packet


class TestAll(unittest.TestCase):
    """Tests packing and unpacking of HeyMac, APv6 and UDP layers together.
    Each test function should test pack and unpack of the same data.
    """

    def test_mac_min(self):
        fmac = HeymacFrame(HeymacFrame.PID_IDENT_HEYMAC, HeymacFrameFctl.NONE)
        b = bytes(fmac)
        self.assertEqual(b, b"\xe0\x00")

        fmac = HeymacFrame.parse(b)
        self.assertEqual(fmac.pid, fmac.PID_IDENT_HEYMAC)
        self.assertFalse(fmac.is_extended())
        self.assertFalse(fmac.is_long_addrs())
        self.assertFalse(fmac.is_netid_present())
        self.assertFalse(fmac.is_daddr_present())
        self.assertFalse(fmac.is_ies_present())
        self.assertFalse(fmac.is_saddr_present())
        self.assertFalse(fmac.is_mhop())
        self.assertFalse(fmac.is_pending_set())
        self.assertEqual(fmac.netid, None)
        self.assertEqual(fmac.daddr, None)
        self.assertEqual(fmac.saddr, None)
        self.assertEqual(fmac.payld, None)

    def test_mac_net_min(self):
        fmac = HeymacFrame(HeymacFrame.PID_IDENT_HEYMAC, HeymacFrameFctl.NONE)
        fmac.payld = APv6Packet()
        b = bytes(fmac)
        self.assertEqual(b, b"\xe0\x00\xD7")

        fmac = HeymacFrame.parse(b)
        self.assertEqual(fmac.pid, fmac.PID_IDENT_HEYMAC)
        self.assertFalse(fmac.is_extended())
        self.assertFalse(fmac.is_long_addrs())
        self.assertFalse(fmac.is_netid_present())
        self.assertFalse(fmac.is_daddr_present())
        self.assertFalse(fmac.is_ies_present())
        self.assertFalse(fmac.is_saddr_present())
        self.assertFalse(fmac.is_mhop())
        self.assertFalse(fmac.is_pending_set())
        self.assertEqual(fmac.netid, None)
        self.assertEqual(fmac.daddr, None)
        self.assertEqual(fmac.saddr, None)
        # Unpack APv6Packet
        fnet = fmac.payld
        self.assertEqual(type(fnet), APv6Packet)
        self.assertEqual(fnet.hdr, b"\xD7")
        self.assertEqual(fnet.hops, b"\x01")
        self.assertEqual(fnet.saddr, b"")
        self.assertEqual(fnet.daddr, b"")
        self.assertEqual(fnet.payld, b"")

"""
    def test_mac_net_udp_min(self):
        fmac = HeymacFrame(fctl_type=HeymacFrame.FCTL_TYPE_NET)
        fnet = APv6Packet()
        fudp = heymac.APv6Udp(src_port=0xF0B0, dst_port=0xF0B0)
        fmac.data = fnet
        fnet.data = fudp
        b = bytes(fmac)
        self.assertEqual(b, b"\xe2\x80\xD7\xF7\x00")

        fmac = HeymacFrame.parse(b)
        self.assertEqual(fmac.pv_pid, fmac.PV_PID_IDENT_HEYMAC)
        self.assertEqual(fmac.pv_ver, fmac.PV_VER_HEYMAC2)
        self.assertEqual(fmac.fctl_type, HeymacFrame.FCTL_TYPE_NET)
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
        # Unpack APv6Packet
        fnet = fmac.data
        self.assertEqual(type(fnet), APv6Packet)
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


    def test_mac_net_udp_to_root(self):
        fmac = HeymacFrame(
            fctl_type=HeymacFrame.FCTL_TYPE_NET,
            pend=0,
            saddr=b"\x35\x16"
            )
        fnet = APv6Packet()
        fudp = heymac.APv6Udp(
            src_port=0xF0B6,
            dst_port=0xF0B0,
            data=b"UdpData"
        )
        fmac.data = fnet
        fnet.data = fudp
        b = bytes(fmac)
        self.assertEqual(b, b"\xe2\x81\x35\x16\xD7\xF7\x60UdpData")

        fmac = HeymacFrame.parse(b)
        self.assertEqual(fmac.pv_pid, fmac.PV_PID_IDENT_HEYMAC)
        self.assertEqual(fmac.pv_ver, fmac.PV_VER_HEYMAC2)
        self.assertEqual(fmac.fctl_type, HeymacFrame.FCTL_TYPE_NET)
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
        # Unpack APv6Packet
        fnet = fmac.data
        self.assertEqual(type(fnet), APv6Packet)
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


    def test_mac_net_udp_to_node(self):
        fmac = HeymacFrame(
            fctl_type=HeymacFrame.FCTL_TYPE_NET,
            pend=0,
            saddr=b"\x35\x16",
            daddr=b"\x83\x11"
            )
        fnet = APv6Packet()
        fudp = heymac.APv6Udp(
            src_port=0xF0BA,
            dst_port=0xF0BF,
            data=b"nodedata"
        )
        fmac.data = fnet
        fnet.data = fudp
        b = bytes(fmac)
        self.assertEqual(b, b"\xe2\x85\x83\x11\x35\x16\xD7\xF7\xAFnodedata")

        fmac = HeymacFrame.parse(b)
        self.assertEqual(fmac.pv_pid, fmac.PV_PID_IDENT_HEYMAC)
        self.assertEqual(fmac.pv_ver, fmac.PV_VER_HEYMAC2)
        self.assertEqual(fmac.fctl_type, HeymacFrame.FCTL_TYPE_NET)
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
        # Unpack APv6Packet
        fnet = fmac.data
        self.assertEqual(type(fnet), APv6Packet)
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


    def test_mac_net_udp_to_google(self):
        fmac = HeymacFrame(
            fctl_type=HeymacFrame.FCTL_TYPE_NET,
            pend=0,
            saddr=b"\x35\x16",
            )
        google_ipv6_addr = b"\x20\x01\x48\x60\x48\x60\x00\x00\x00\x00\x00\x00\x00\x00\x88\x88"
        fnet = APv6Packet(
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

        fmac = HeymacFrame.parse(b)
        self.assertEqual(fmac.pv_pid, fmac.PV_PID_IDENT_HEYMAC)
        self.assertEqual(fmac.pv_ver, fmac.PV_VER_HEYMAC2)
        self.assertEqual(fmac.fctl_type, HeymacFrame.FCTL_TYPE_NET)
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
        # Unpack APv6Packet
        fnet = fmac.data
        self.assertEqual(type(fnet), APv6Packet)
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
"""

if __name__ == "__main__":
    unittest.main()
