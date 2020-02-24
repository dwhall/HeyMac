#!/usr/bin/env python3


import unittest

import heymac


class TestHeyMacCmds(unittest.TestCase):
    """Tests the mac_frame.HeyMacFrame packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """

    def test_sbcn(self,):
        # Pack
        bcn = heymac.HeyMacCmdSbcn(
            bcn_en=1,
            sf_order=7,
            eb_order=5,
            dscpln=2,
            caps=3,
            status=4,
            asn=42,
        )
        b = bytes(bcn)
        self.assertEqual(b, b"\x81\xd7\x02\x03\x04\x00\x00\x00\x2a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        # Unpack
        f = heymac.HeyMacCmdSbcn(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_SBCN)
        self.assertEqual(f.dscpln, 2)
        self.assertEqual(f.caps, 3)
        self.assertEqual(f.status, 4)
        self.assertEqual(f.asn, 42)


    def test_sbcn_slots(self,):
        # Pack
        bcn = heymac.HeyMacCmdSbcn(
            bcn_en=1,
            sf_order=7,
            eb_order=5,
            dscpln=2,
            caps=3,
            status=4,
            asn=42,
        )
        bcn.tx_slots = bytearray(range(16))
        bcn.ngbr_tx_slots = bytearray(range(0x80, 0x80 + 16))
        b = bytes(bcn)
        self.assertEqual(b, b"\x81\xd7\x02\x03\x04\x00\x00\x00\x2a\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f")
        # Unpack
        f = heymac.HeyMacCmdSbcn(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_SBCN)
        self.assertEqual(f.dscpln, 2)
        self.assertEqual(f.caps, 3)
        self.assertEqual(f.status, 4)
        self.assertEqual(f.asn, 42)


    def test_ebcn(self,):
        # Pack
        ebcn = heymac.HeyMacCmdEbcn(
            bcn_en=1,
            sf_order=7,
            eb_order=5,
            dscpln=2,
            caps=3,
            status=4,
            asn=42,
        )
        ebcn.station_id = b"KC4KSU-123"
        ebcn.ngbrs = []
        ebcn.ntwks = []
        b = bytes(ebcn)
        self.assertEqual(b, b"\x82\xd7\x02\x03\x04\x00\x00\x00\x2a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"KC4KSU-123\x00\x00\x00")
        # Unpack
        f = heymac.HeyMacCmdEbcn(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_EBCN)
        self.assertEqual(f.dscpln, 2)
        self.assertEqual(f.caps, 3)
        self.assertEqual(f.status, 4)
        self.assertEqual(f.asn, 42)
        self.assertEqual(f.station_id, b"KC4KSU-123\x00")
        self.assertEqual(f.ngbrs, [])
        self.assertEqual(f.ntwks, [])


    def test_ebcn_ngbrs(self,):
        # Pack
        ebcn = heymac.HeyMacCmdEbcn(
            bcn_en=1,
            sf_order=7,
            eb_order=5,
            dscpln=2,
            caps=3,
            status=4,
            asn=42,
        )
        ebcn.station_id = b"KC4KSU-123"
        ebcn.ngbrs = [(b"\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8", 22, 33),]
        ebcn.ntwks = []
        b = bytes(ebcn)
        self.assertEqual(b, b"\x82\xd7\x02\x03\x04\x00\x00\x00\x2a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"KC4KSU-123\x00"
                b"\x01\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\x16\x21"
                b"\x00")
        # Unpack
        f = heymac.HeyMacCmdEbcn(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_EBCN)
        self.assertEqual(f.dscpln, 2)
        self.assertEqual(f.caps, 3)
        self.assertEqual(f.status, 4)
        self.assertEqual(f.asn, 42)
        self.assertEqual(f.station_id, b"KC4KSU-123\x00")
        self.assertEqual(f.ngbrs, [(b"\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8", 22, 33),])
        self.assertEqual(f.ntwks, [])


    def test_ebcn_ngbrs_ntwks(self,):
        # Pack
        ebcn = heymac.HeyMacCmdEbcn(
            bcn_en=1,
            sf_order=7,
            eb_order=5,
            dscpln=2,
            caps=3,
            status=4,
            asn=42,
        )
        ebcn.station_id = b"KC4KSU-123"
        ebcn.ngbrs = [
            (b"\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8", 22, 33),
            (b"\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8", 44, 55),]
        ebcn.ntwks = [(0x1001, b"\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8", 0x4321),]
        b = bytes(ebcn)
        self.assertEqual(b, b"\x82\xd7\x02\x03\x04\x00\x00\x00\x2a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"KC4KSU-123\x00"
                b"\x02\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\x16\x21\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\x2c\x37"
                b"\x01\x10\x01\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\x43\x21")
        # Unpack
        f = heymac.HeyMacCmdEbcn(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_EBCN)
        self.assertEqual(f.dscpln, 2)
        self.assertEqual(f.caps, 3)
        self.assertEqual(f.status, 4)
        self.assertEqual(f.asn, 42)
        self.assertEqual(f.station_id, b"KC4KSU-123\x00")
        self.assertEqual(f.ngbrs, [
            (b"\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8", 22, 33),
            (b"\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8", 44, 55),])
        self.assertEqual(f.ntwks, [(0x1001, b"\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8", 0x4321),])


    def test_txt_empty(self,):
        # Pack
        txt = heymac.HeyMacCmdTxt(msg=b"")
        b = bytes(txt)
        self.assertEqual(b, b"\x83")
        # Unpack
        f = heymac.HeyMacCmdTxt(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_TXT)
        self.assertEqual(f.msg, b"")


    def test_txt(self,):
        # Pack
        txt = heymac.HeyMacCmdTxt(msg=b"Hell, oh! whirled")
        b = bytes(txt)
        self.assertEqual(b, b"\x83Hell, oh! whirled")
        # Unpack
        f = heymac.HeyMacCmdTxt(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_TXT)
        self.assertEqual(f.msg, b"Hell, oh! whirled")


if __name__ == '__main__':
    unittest.main()
