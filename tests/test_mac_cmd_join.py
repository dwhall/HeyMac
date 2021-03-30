#!/usr/bin/env python3


import unittest

import heymac


class TestHeyMacCmdJoin(unittest.TestCase):
    """Tests the mac_cmd_join.HeyMacCmdJoin* classes packing and unpacking.
    Each test function should test pack and unpack of the same data.
    """

    def test_join_rqst(self):
        # Pack
        cmd_join_rqst = heymac.HeyMacCmdJoinRequest()
        cmd_join_rqst.net_id = 0x1234
        b = bytes(cmd_join_rqst)
        self.assertEqual(b, b"\x85\x01\x12\x34")
        # Unpack
        f = heymac.HeyMacCmdJoinRequest(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_JOIN)
        self.assertEqual(f.mid, heymac.HeyMacCmdJoin.MID_RQST)
        self.assertEqual(f.net_id, 0x1234)
        # Unpack
        f = heymac.HeyMacCmd.get_instance(b)
        self.assertIsInstance(f, heymac.HeyMacCmdJoinRequest)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_JOIN)
        self.assertEqual(f.mid, heymac.HeyMacCmdJoin.MID_RQST)
        self.assertEqual(f.net_id, 0x1234)


    def test_join_rspd(self):
        # Pack
        cmd_join_rqst = heymac.HeyMacCmdJoinRespond()
        cmd_join_rqst.short_addr = 0x1000
        b = bytes(cmd_join_rqst)
        self.assertEqual(b, b"\x85\x02\x10\x00")
        # Unpack
        f = heymac.HeyMacCmdJoinRespond(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_JOIN)
        self.assertEqual(f.mid, heymac.HeyMacCmdJoin.MID_RSPD)
        self.assertEqual(f.short_addr, 0x1000)
        # Unpack
        f = heymac.HeyMacCmd.get_instance(b)
        self.assertIsInstance(f, heymac.HeyMacCmdJoinRespond)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_JOIN)
        self.assertEqual(f.mid, heymac.HeyMacCmdJoin.MID_RSPD)
        self.assertEqual(f.short_addr, 0x1000)


    def test_join_cnfm(self):
        # Pack
        cmd_join_cnfm = heymac.HeyMacCmdJoinConfirm()
        cmd_join_cnfm.short_addr = 0x2000
        b = bytes(cmd_join_cnfm)
        self.assertEqual(b, b"\x85\x03\x20\x00")
        # Unpack
        f = heymac.HeyMacCmdJoinConfirm(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_JOIN)
        self.assertEqual(f.mid, heymac.HeyMacCmdJoin.MID_CNFM)
        self.assertEqual(f.short_addr, 0x2000)
        # Unpack
        f = heymac.HeyMacCmd.get_instance(b)
        self.assertIsInstance(f, heymac.HeyMacCmdJoinConfirm)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_JOIN)
        self.assertEqual(f.mid, heymac.HeyMacCmdJoin.MID_CNFM)
        self.assertEqual(f.short_addr, 0x2000)


    def test_join_rjct(self):
        # Pack
        cmd_join_rjct = heymac.HeyMacCmdJoinReject()
        b = bytes(cmd_join_rjct)
        self.assertEqual(b, b"\x85\x04")
        # Unpack
        f = heymac.HeyMacCmdJoinReject(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_JOIN)
        self.assertEqual(f.mid, heymac.HeyMacCmdJoin.MID_RJCT)
        # Unpack
        f = heymac.HeyMacCmd.get_instance(b)
        self.assertIsInstance(f, heymac.HeyMacCmdJoinReject)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_JOIN)
        self.assertEqual(f.mid, heymac.HeyMacCmdJoin.MID_RJCT)


    def test_join_leav(self):
        # Pack
        cmd_join_leav = heymac.HeyMacCmdJoinLeave()
        b = bytes(cmd_join_leav)
        self.assertEqual(b, b"\x85\x05")
        # Unpack
        f = heymac.HeyMacCmdJoinLeave(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_JOIN)
        self.assertEqual(f.mid, heymac.HeyMacCmdJoin.MID_LEAV)
        # Unpack
        f = heymac.HeyMacCmd.get_instance(b)
        self.assertIsInstance(f, heymac.HeyMacCmdJoinLeave)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_JOIN)
        self.assertEqual(f.mid, heymac.HeyMacCmdJoin.MID_LEAV)


    def test_join_drop(self):
        # Pack
        cmd_join_drop = heymac.HeyMacCmdJoinDrop()
        b = bytes(cmd_join_drop)
        self.assertEqual(b, b"\x85\x06")
        # Unpack
        f = heymac.HeyMacCmdJoinDrop(b)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_JOIN)
        self.assertEqual(f.mid, heymac.HeyMacCmdJoin.MID_DROP)
        # Unpack
        f = heymac.HeyMacCmd.get_instance(b)
        self.assertIsInstance(f, heymac.HeyMacCmdJoinDrop)
        self.assertEqual(f.cmd, heymac.HeyMacCmd.CID_JOIN)
        self.assertEqual(f.mid, heymac.HeyMacCmdJoin.MID_DROP)


if __name__ == '__main__':
    unittest.main()
