#!/usr/bin/env python3


import unittest

import mac_cmds
import mac_frame


class TestHeyMacCmds(unittest.TestCase):
    """Tests the mac_frame.HeyMacFrame packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """

    def test_sbcn_happy(self,):
        bcn = mac_cmds.HeyMacCmdSbcn(
            bcn_en=1,
            sf_order=7,
            eb_order=5,
            dscpln=2,
            caps=3,
            status=4,
            asn=42,
        )
        bcn.tx_slots = list(range(16))
        bcn.ngbr_tx_slots = list(range(0x80, 0x80 + 16))

        b = bytes(bcn)
        self.assertEqual(b, b"\x01\xd7\x02\x03\x04\x00\x00\x00\x2a\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f")

        f = mac_cmds.HeyMacCmdSbcn(b)
        self.assertEqual(f.cmd, mac_cmds.HeyMacCmdId.SBCN)
        self.assertEqual(f.dscpln, 2)
        self.assertEqual(f.caps, 3)
        self.assertEqual(f.status, 4)
        self.assertEqual(f.asn, 42)

    def test_sbcn_happy2(self,):
        bcn = mac_cmds.HeyMacCmdSbcn(
            bcn_en=1,
            sf_order=7,
            eb_order=5,
            dscpln=2,
            caps=3,
            status=4,
            asn=42,
        )
        bcn.tx_slots = list(range(16))
        bcn.ngbr_tx_slots = list(range(0x80, 0x80 + 16))

        b = bytes(bcn)
        self.assertEqual(b, b"\x01\xd7\x02\x03\x04\x00\x00\x00\x2a\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f")

        f = mac_cmds.HeyMacCmdSbcn(b)
        self.assertEqual(f.cmd, mac_cmds.HeyMacCmdId.SBCN)
        self.assertEqual(f.dscpln, 2)
        self.assertEqual(f.caps, 3)
        self.assertEqual(f.status, 4)
        self.assertEqual(f.asn, 42)

    def test_txt(self,):
        txt = mac_cmds.HeyMacCmdTxt(msg=b"Hell, oh! whirled")

        b = bytes(txt)
        self.assertEqual(b, b"\x03Hell, oh! whirled")

        f = mac_cmds.HeyMacCmdTxt(b)
        self.assertEqual(f.cmd, mac_cmds.HeyMacCmdId.TXT)
        self.assertEqual(f.msg, b"Hell, oh! whirled")


if __name__ == '__main__':
    unittest.main()
