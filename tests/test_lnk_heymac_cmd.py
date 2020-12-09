#!/usr/bin/env python3


import unittest

from lnk_heymac.lnk_heymac_cmd import *


class TestHeyMacCmd(unittest.TestCase):
    """Tests the HeymacCmd building and serializing."""

    def test_txt(self,):
        # Build and serialize
        c = HeymacCmdTxt(b"Hello world")
        b = bytes(c)
        self.assertEqual(b, b"\x83Hello world")
        # Parse and test
        c = HeymacCmd.parse(b)
        self.assertIs(type(c), HeymacCmdTxt)
        self.assertEqual(c.data, b"Hello world")


    def test_bcn(self,):
        # Build and serialize
        c = HeymacCmdCsmaBcn(b"\x00\x00", b"\x00\x00", b"\x00", b"\x00")
        b = bytes(c)
        self.assertEqual(b, b"\x84\x00\x00\x00\x00\x00\x00")
        # Parse and test
        c = HeymacCmd.parse(b)
        self.assertIs(type(c), HeymacCmdCsmaBcn)
        self.assertEqual(c.data, b"\x00\x00\x00\x00\x00\x00")


if __name__ == '__main__':
    unittest.main()
