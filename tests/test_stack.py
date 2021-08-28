#!/usr/bin/env python3


from heymac.net.apv6_pkt import UdpDatagram
import unittest

from heymac.lnk import *
from heymac.net import APv6Packet, UdpDatagram


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
        self.assertIsNone(fmac.netid)
        self.assertIsNone(fmac.daddr)
        self.assertIsNone(fmac.saddr)
        self.assertIsNone(fmac.payld)

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
        self.assertIsNone(fmac.netid)
        self.assertIsNone(fmac.daddr)
        self.assertIsNone(fmac.saddr)

        fnet = fmac.payld
        self.assertEqual(type(fnet), APv6Packet)
        self.assertEqual(fnet.hdr, b"\xD7")
        self.assertEqual(fnet.hops, b"\x01")
        self.assertIsNone(fnet.saddr)
        self.assertIsNone(fnet.daddr)
        self.assertIsNone(fnet.payld)

    def test_mac_net_udp_min(self):
        fmac = HeymacFrame(HeymacFrame.PID_IDENT_HEYMAC
                           | HeymacFrame.PID_TYPE_CSMA)
        fnet = APv6Packet()
        fudp = UdpDatagram(src_port=0xF0B0, dst_port=0xF0B0)
        fmac.payld = fnet
        fnet.payld = fudp
        b = bytes(fmac)
        self.assertEqual(b, b"\xe4\x00\xD7\xF7\x00")

        fmac = HeymacFrame.parse(b)
        self.assertEqual(fmac.pid, fmac.PID_IDENT_HEYMAC | fmac.PID_TYPE_CSMA)
        self.assertFalse(fmac.is_extended())
        self.assertFalse(fmac.is_long_addrs())
        self.assertFalse(fmac.is_netid_present())
        self.assertFalse(fmac.is_daddr_present())
        self.assertFalse(fmac.is_ies_present())
        self.assertFalse(fmac.is_saddr_present())
        self.assertFalse(fmac.is_mhop())
        self.assertFalse(fmac.is_pending_set())
        self.assertIsNone(fmac.netid)
        self.assertIsNone(fmac.daddr)
        self.assertIsNone(fmac.saddr)

        fnet = fmac.payld
        self.assertEqual(type(fnet), APv6Packet)
        self.assertEqual(fnet.hdr, b"\xD7")
        self.assertEqual(fnet.hops, b"\x01")
        self.assertIsNone(fnet.saddr)
        self.assertIsNone(fnet.daddr)

        fudp = fnet.payld
        self.assertEqual(type(fudp), UdpDatagram)
        self.assertEqual(fudp.hdr, b"\xF7")
        self.assertEqual(fudp.src_port, b"\xF0\xB0")
        self.assertEqual(fudp.dst_port, b"\xF0\xB0")


    def test_mac_net_udp_to_root(self):
        fmac = HeymacFrame(HeymacFrame.PID_IDENT_HEYMAC
                           | HeymacFrame.PID_TYPE_CSMA,
                          saddr=b"\x35\x16")
        fnet = APv6Packet()
        fudp = UdpDatagram(src_port=0xF0B6,
                           dst_port=0xF0B0,
                           payld=b"UdpData")
        fmac.payld = fnet
        fnet.payld = fudp
        b = bytes(fmac)
        self.assertEqual(b, b"\xe4\x04\x35\x16\xD7\xF7\x60UdpData")

        fmac = HeymacFrame.parse(b)
        self.assertEqual(fmac.pid, fmac.PID_IDENT_HEYMAC | fmac.PID_TYPE_CSMA)
        self.assertFalse(fmac.is_extended())
        self.assertFalse(fmac.is_long_addrs())
        self.assertFalse(fmac.is_netid_present())
        self.assertFalse(fmac.is_daddr_present())
        self.assertFalse(fmac.is_ies_present())
        self.assertTrue(fmac.is_saddr_present())
        self.assertFalse(fmac.is_mhop())
        self.assertFalse(fmac.is_pending_set())
        self.assertIsNone(fmac.netid)
        self.assertIsNone(fmac.daddr)
        self.assertEqual(fmac.saddr, b"\x35\x16")

        fnet = fmac.payld
        self.assertEqual(type(fnet), APv6Packet)
        self.assertEqual(fnet.hdr, b"\xD7")
        self.assertEqual(fnet.hops, b"\x01")
        self.assertIsNone(fnet.saddr)
        self.assertIsNone(fnet.daddr)

        fudp = fnet.payld
        self.assertEqual(type(fudp), UdpDatagram)
        self.assertEqual(fudp.hdr, b"\xF7")
        self.assertEqual(fudp.src_port, b"\xF0\xB6")
        self.assertEqual(fudp.dst_port, b"\xF0\xB0")
        self.assertEqual(fudp.payld, b"UdpData")


    def test_mac_net_udp_to_node(self):
        fmac = HeymacFrame(HeymacFrame.PID_IDENT_HEYMAC
                           | HeymacFrame.PID_TYPE_CSMA,
                           saddr=b"\x35\x16",
                           daddr=b"\x83\x11")
        fnet = APv6Packet()
        fudp = UdpDatagram(src_port=0xF0BA,
                           dst_port=0xF0BF,
                           payld=b"nodedata")
        fmac.payld = fnet
        fnet.payld = fudp
        b = bytes(fmac)
        self.assertEqual(b, b"\xe4\x14\x83\x11\x35\x16\xD7\xF7\xAFnodedata")

        fmac = HeymacFrame.parse(b)
        self.assertEqual(fmac.pid, fmac.PID_IDENT_HEYMAC | fmac.PID_TYPE_CSMA)
        self.assertFalse(fmac.is_extended())
        self.assertFalse(fmac.is_long_addrs())
        self.assertFalse(fmac.is_netid_present())
        self.assertTrue(fmac.is_daddr_present())
        self.assertFalse(fmac.is_ies_present())
        self.assertTrue(fmac.is_saddr_present())
        self.assertFalse(fmac.is_mhop())
        self.assertFalse(fmac.is_pending_set())
        self.assertIsNone(fmac.netid)
        self.assertEqual(fmac.daddr, b"\x83\x11")
        self.assertEqual(fmac.saddr, b"\x35\x16")
        self.assertIsInstance(fmac.payld, APv6Packet)

        fnet = fmac.payld
        self.assertEqual(type(fnet), APv6Packet)
        self.assertEqual(fnet.hdr, b"\xD7")
        self.assertEqual(fnet.hops, b"\x01")
        self.assertIsNone(fnet.saddr)
        self.assertIsNone(fnet.daddr)

        fudp = fnet.payld
        self.assertEqual(type(fudp), UdpDatagram)
        self.assertEqual(fudp.hdr, b"\xF7")
        self.assertEqual(fudp.src_port, b"\xF0\xBA")
        self.assertEqual(fudp.dst_port, b"\xF0\xBF")
        self.assertEqual(fudp.payld, b"nodedata")


    def test_mac_net_udp_to_google(self):
        fmac = HeymacFrame(HeymacFrame.PID_IDENT_HEYMAC
                           | HeymacFrame.PID_TYPE_CSMA,
                           saddr=b"\x35\x16")
        google_ipv6_addr = b"\x20\x01\x48\x60\x48\x60\x00\x00\x00\x00\x00\x00\x00\x00\x88\x88"
        fnet = APv6Packet(daddr=google_ipv6_addr)
        fudp = UdpDatagram(src_port=0xF0B0,
                           dst_port=53,
                           payld=b"DnsRequest")
        fmac.payld = fnet
        fnet.payld = fudp
        b = bytes(fmac)
        self.assertEqual(b,
                         b"\xe4\x04\x35\x16\xD6"
                         + google_ipv6_addr
                         + b"\xF6\xB0\x00\x35DnsRequest")

        fmac = HeymacFrame.parse(b)
        self.assertEqual(fmac.pid, fmac.PID_IDENT_HEYMAC | fmac.PID_TYPE_CSMA)
        self.assertFalse(fmac.is_extended())
        self.assertFalse(fmac.is_long_addrs())
        self.assertFalse(fmac.is_netid_present())
        self.assertFalse(fmac.is_daddr_present())
        self.assertFalse(fmac.is_ies_present())
        self.assertTrue(fmac.is_saddr_present())
        self.assertFalse(fmac.is_mhop())
        self.assertFalse(fmac.is_pending_set())
        self.assertIsNone(fmac.netid)
        self.assertIsNone(fmac.daddr)
        self.assertEqual(fmac.saddr, b"\x35\x16")
        self.assertIsInstance(fmac.payld, APv6Packet)

        fnet = fmac.payld
        self.assertEqual(type(fnet), APv6Packet)
        self.assertEqual(fnet.hdr, b"\xD6")
        self.assertEqual(fnet.hops, b"\x01")
        self.assertIsNone(fnet.saddr)
        self.assertEqual(fnet.daddr, google_ipv6_addr)

        fudp = fnet.payld
        self.assertEqual(type(fudp), UdpDatagram)
        self.assertEqual(fudp.hdr, b"\xF6")
        self.assertEqual(fudp.src_port, b"\xF0\xB0")
        self.assertEqual(fudp.dst_port, b"\x00\x35")
        self.assertEqual(fudp.payld, b"DnsRequest")


if __name__ == "__main__":
    unittest.main()
