#!/usr/bin/env python3


import unittest

from heymac.lnk.heymac_cmd import *


PUB_KEY = b"\xb2R\x96\xff\xdeb\x84S\xe6\xcd\x8cU\x84W!\xaf\xa8,Vf\\\x8c\x03\x7f'\x1d\x88^8\x07?U\xbbl\x18\xec\xc8*PC\x88}'\xf1\x84\xd7\xed\xc6\x9bH9\xfa\xa0\xe0\xbdS5\xbf\x16h\xc8\x0f}\x9d\xc3\xe9\x10:beb~\xf5\x9d\x1b\xcf}\xdd\x93\xbc(\xf8\x19\x1e\xb0Hf\xaf1\xd3\x9e\xbb\xcaG\t\n"


class TestHeyMacCmd(unittest.TestCase):
    """Tests the HeymacCmd building and serializing."""

    def test_txt(self):
        # Build and serialize
        c = HeymacCmdTxt(FLD_MSG=b"Hello world")
        b = bytes(c)
        self.assertEqual(b, b"\x83Hello world")
        # Parse and test
        c = HeymacCmd.parse(b)
        self.assertIs(type(c), HeymacCmdTxt)
        self.assertEqual(c.get_field(HeymacCmd.FLD_MSG), b"Hello world")


    def test_bcn(self):
        # Build and serialize
        c = HeymacCmdBcn(
            FLD_CAPS=0x0102,
            FLD_STATUS=0x0304,
            FLD_CALLSIGN_SSID=b"EX4MPL-227",
            FLD_PUB_KEY=PUB_KEY)
        b = bytes(c)
        self.assertEqual(b, b"\x84\x01\x02\x03\x04EX4MPL-227      " + PUB_KEY)
        # Parse and test
        c = HeymacCmd.parse(b)
        self.assertIs(type(c), HeymacCmdBcn)
        self.assertEqual(c.get_field(HeymacCmd.FLD_CAPS), 0x0102)
        self.assertEqual(c.get_field(HeymacCmd.FLD_STATUS), 0x0304)
        self.assertEqual(c.get_field(HeymacCmd.FLD_CALLSIGN_SSID), "EX4MPL-227")
        self.assertEqual(c.get_field(HeymacCmd.FLD_PUB_KEY), PUB_KEY)

class _Deprecated_MovingToNetLayer:
    def test_join_rqst(self):
        # Build and serialize
        c = HeymacCmdJoinRqst(FLD_NET_ID=0x0102)
        b = bytes(c)
        self.assertEqual(b, b"\x85\x01\x01\x02")
        # Parse and test
        c = HeymacCmd.parse(b)
        self.assertIs(type(c), HeymacCmdJoinRqst)


    def test_join_rqst_bad_fld(self):
        def _join_rqst_bad_fld():
            c = HeymacCmdJoinRqst(FLD_BOB=0x0102)
        self.assertRaises(HeymacCmdError, _join_rqst_bad_fld)


    def test_join_rqst_bad_data(self):
        # Bad CMD_ID
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\xFF\x01\x01\x02")
        # Bad SUB_ID
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\xFF\x01\x02")
        # Not enough data
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\x01\x01")
        # Too much data
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\x01\x01\x02\x03")


    def test_join_acpt(self):
        # Build and serialize
        c = HeymacCmdJoinAcpt(FLD_NET_ID=0x0102, FLD_NET_ADDR=0x0123)
        b = bytes(c)
        self.assertEqual(b, b"\x85\x02\x01\x02\x01\x23")
        # Parse and test
        c = HeymacCmd.parse(b)
        self.assertIs(type(c), HeymacCmdJoinAcpt)


    def test_join_acpt_bad_fld(self):
        def _join_acpt_bad_fld():
            c = HeymacCmdJoinAcpt(FLD_NET_ID=0x0102, FLD_BOB=0x0304)
        self.assertRaises(HeymacCmdError, _join_acpt_bad_fld)


    def test_join_acpt_bad_data(self):
        # Bad CMD_ID
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\xFF\x02\x01\x02\x03\x04")
        # Bad SUB_ID
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\xFF\x01\x02\x03\x04")
        # Not enough data
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\x02\x01\x02\x03")
        # Too much data
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\x02\x01\x02\x03\x04\x05")


    def test_join_cnfm(self):
        # Build and serialize
        c = HeymacCmdJoinCnfm(FLD_NET_ID=0x0102, FLD_NET_ADDR=0x0123)
        b = bytes(c)
        self.assertEqual(b, b"\x85\x03\x01\x02\x01\x23")
        # Parse and test
        c = HeymacCmd.parse(b)
        self.assertIs(type(c), HeymacCmdJoinCnfm)


    def test_join_cnfm_bad_fld(self):
        def _join_cnfm_bad_fld():
            c = HeymacCmdJoinCnfm(FLD_NET_ID=0x0102, FLD_BOB=0x0304)
        self.assertRaises(HeymacCmdError, _join_cnfm_bad_fld)


    def test_join_cnfm_bad_data(self):
        # Bad CMD_ID
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\xFF\x03\x01\x02\x03\x04")
        # Bad SUB_ID
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\xFF\x01\x02\x03\x04")
        # Not enough data
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\x03\x01\x02\x03")
        # Too much data
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\x03\x01\x02\x03\x04\x05")


    def test_join_rjct(self):
        # Build and serialize
        c = HeymacCmdJoinRjct() # no kwargs means ctor expecting bytes
        b = bytes(c)
        self.assertEqual(b, b"\x85\x04")
        # Parse and test
        c = HeymacCmd.parse(b)
        self.assertIs(type(c), HeymacCmdJoinRjct)


    def test_join_rjct_bad_fld(self):
        def _join_rjct_bad_fld():
            c = HeymacCmdJoinRjct(FLD_BOB=0x0304)
        self.assertRaises(HeymacCmdError, _join_rjct_bad_fld)


    def test_join_rjct_bad_data(self):
        # Bad CMD_ID
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\xFF\x04")
        # Bad SUB_ID
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\xFF")
        # Not enough data
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85")
        # Too much data
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\x04\x05")


    def test_join_leav(self):
        # Build and serialize
        c = HeymacCmdJoinLeav()
        b = bytes(c)
        self.assertEqual(b, b"\x85\x05")
        # Parse and test
        c = HeymacCmd.parse(b)
        self.assertIs(type(c), HeymacCmdJoinLeav)


    def test_join_leav_bad_fld(self):
        def _join_leav_bad_fld():
            c = HeymacCmdJoinLeav(FLD_BOB=0x0304)
        self.assertRaises(HeymacCmdError, _join_leav_bad_fld)


    def test_join_leav_bad_data(self):
        # Bad CMD_ID
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\xFF\x05")
        # Bad SUB_ID
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\xFF")
        # Not enough data
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85")
        # Too much data
        self.assertRaises(HeymacCmdError, HeymacCmd.parse, b"\x85\x05\x05")


if __name__ == '__main__':
    unittest.main()
