#!/usr/bin/env python3


import unittest

import mac_cmds
import mac_frame


class TestHeyMacCmds(unittest.TestCase):
    """Tests the mac_frame.HeyMacFrame packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """

    def test_small_bcn_happy(self,):
        bcn = mac_cmds.CmdPktSmallBcn(
            _frame_spec = mac_cmds.CmdPktSmallBcn.FRAME_SPEC_BCN_EN_MASK \
                    | 5 << mac_cmds.CmdPktSmallBcn.FRAME_SPEC_SF_ORDER_SHIFT \
                    | 10,
            dscpln=2,
            caps=3,
            status=4,
            asn=42,
        )
        bcn.tx_slots = list(range(4))
        bcn.ngbr_tx_slots = list(range(0x80, 0x80 + 4))

        b = bytes(bcn)
        self.assertEqual(b, b"\x01\xda\x02\x03\x04\x00\x00\x00\x2a\x00\x01\x02\x03\x80\x81\x82\x83")

        f = mac_cmds.CmdPktSmallBcn(b)
        self.assertEqual(f.cmd, mac_cmds.HeyMacCmdId.SM_BCN)
        self.assertEqual(f.dscpln, 2)
        self.assertEqual(f.caps, 3)
        self.assertEqual(f.status, 4)
        self.assertEqual(f.asn, 42)

    def test_small_bcn_happy2(self,):
        bcn = mac_cmds.CmdPktSmallBcn(
            bcn_en=1,
            sf_order=5,
            eb_order=10,
            dscpln=2,
            caps=3,
            status=4,
            asn=42,
        )
        bcn.tx_slots = list(range(4))
        bcn.ngbr_tx_slots = list(range(0x80, 0x80 + 4))

        b = bytes(bcn)
        self.assertEqual(b, b"\x01\xda\x02\x03\x04\x00\x00\x00\x2a\x00\x01\x02\x03\x80\x81\x82\x83")

        f = mac_cmds.CmdPktSmallBcn(b)
        self.assertEqual(f.cmd, mac_cmds.HeyMacCmdId.SM_BCN)
        self.assertEqual(f.dscpln, 2)
        self.assertEqual(f.caps, 3)
        self.assertEqual(f.status, 4)
        self.assertEqual(f.asn, 42)

    def test_txt(self,):
        txt = mac_cmds.CmdPktTxt(msg=b"Hell, oh! whirled")

        b = bytes(txt)
        self.assertEqual(b, b"\x03Hell, oh! whirled")

        f = mac_cmds.CmdPktTxt(b)
        self.assertEqual(f.cmd, mac_cmds.HeyMacCmdId.TXT)
        self.assertEqual(f.msg, b"Hell, oh! whirled")


if __name__ == '__main__':
    unittest.main()
