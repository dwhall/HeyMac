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
        self.assertEqual(b, b"\x01\xd7\x02\x03\x04\x00\x00\x00\x2a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        # Unpack
        f = heymac.HeyMacCmdSbcn(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmdId.SBCN)
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
        self.assertEqual(b, b"\x01\xd7\x02\x03\x04\x00\x00\x00\x2a\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f")
        # Unpack
        f = heymac.HeyMacCmdSbcn(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmdId.SBCN)
        self.assertEqual(f.dscpln, 2)
        self.assertEqual(f.caps, 3)
        self.assertEqual(f.status, 4)
        self.assertEqual(f.asn, 42)

    def test_txt_empty(self,):
        # Pack
        txt = heymac.HeyMacCmdTxt(msg=b"")
        b = bytes(txt)
        self.assertEqual(b, b"\x03")
        # Unpack
        f = heymac.HeyMacCmdTxt(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmdId.TXT)
        self.assertEqual(f.msg, b"")

    def test_txt(self,):
        # Pack
        txt = heymac.HeyMacCmdTxt(msg=b"Hell, oh! whirled")
        b = bytes(txt)
        self.assertEqual(b, b"\x03Hell, oh! whirled")
        # Unpack
        f = heymac.HeyMacCmdTxt(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmdId.TXT)
        self.assertEqual(f.msg, b"Hell, oh! whirled")


if __name__ == '__main__':
    unittest.main()
