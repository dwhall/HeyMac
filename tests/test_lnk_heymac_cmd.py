#!/usr/bin/env python3


import unittest

from lnk_heymac.lnk_heymac_cmd import *


class TestHeyMacCmd(unittest.TestCase):
    """Tests the HeymacCmd building and serializing."""

    def test_txt(self,):
        # Build and serialize
        c = HeymacCmdTxt(FLD_MSG=b"Hello world")
        b = bytes(c)
        self.assertEqual(b, b"\x83Hello world")
        # Parse and test
        c = HeymacCmd.parse(b)
        self.assertIs(type(c), HeymacCmdTxt)
        self.assertEqual(c.get_field(HeymacCmd.FLD_MSG), b"Hello world")


    def test_bcn(self,):
        # Build and serialize
        c = HeymacCmdCsmaBcn(
            FLD_CAPS=0x0102,
            FLD_STATUS=0x0304,
            FLD_NETS=((0x0001, b"\xfdnetroot"),),
            FLD_NGBRS=(b"\xfd2345678",))
        b = bytes(c)
        self.assertEqual(b, b"\x84\x01\x02\x03\x04\x01\x00\x01\xfdnetroot\x01\xfd2345678")
        # Parse and test
        c = HeymacCmd.parse(b)
        self.assertIs(type(c), HeymacCmdCsmaBcn)
        self.assertEqual(c.get_field(HeymacCmd.FLD_CAPS), 0x0102)
        self.assertEqual(c.get_field(HeymacCmd.FLD_STATUS), 0x0304)
        self.assertEqual(c.get_field(HeymacCmd.FLD_NETS), (0x0001, b"\xfdnetroot"))
        self.assertEqual(c.get_field(HeymacCmd.FLD_NGBRS), (b"\xfd2345678",))


if __name__ == '__main__':
    unittest.main()
