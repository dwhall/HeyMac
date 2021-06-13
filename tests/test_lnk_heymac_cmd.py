#!/usr/bin/env python3


import unittest

from heymac.lnk import *


PUB_KEY = b"\xb2R\x96\xff\xdeb\x84S\xe6\xcd\x8cU\x84W!" \
          b"\xaf\xa8,Vf\\\x8c\x03\x7f'\x1d\x88^8\x07?" \
          b"U\xbbl\x18\xec\xc8*PC\x88}'\xf1\x84\xd7\xed\xc6" \
          b"\x9bH9\xfa\xa0\xe0\xbdS5\xbf\x16h\xc8\x0f}\x9d" \
          b"\xc3\xe9\x10:beb~\xf5\x9d\x1b\xcf}\xdd\x93\xbc" \
          b"(\xf8\x19\x1e\xb0Hf\xaf1\xd3\x9e\xbb\xcaG\t\n"


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

    def test_txt_no_fld(self):
        with self.assertRaises(HeymacCmdError):
            _ = HeymacCmdTxt()

    def test_txt_extra_fld(self):
        with self.assertRaises(HeymacCmdError):
            _ = HeymacCmdTxt(FLD_MSG=b"Hello world", FLD_CAPS=42)

    def test_txt_wrong_fld(self):
        with self.assertRaises(HeymacCmdError):
            _ = HeymacCmdTxt(FLD_CAPS=42)

    def test_txt_invalid_fld(self):
        with self.assertRaises(HeymacCmdError):
            _ = HeymacCmdTxt(FLD_INVALID=None)

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

    def test_unknown_cmd(self):
        b = b"\xbe\x11\x22"
        c = HeymacCmd.parse(b)
        self.assertIs(type(c), HeymacCmdUnknown)


if __name__ == '__main__':
    unittest.main()
