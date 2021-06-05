#!/usr/bin/env python3


import unittest

from heymac.lnk import HeymacIe, HeymacIeError, \
    HeymacHIeTerm, HeymacHIeSqncNmbr, HeymacHIeCipher, \
    HeymacPIeTerm, HeymacPIeFrag0, HeymacPIeFragN, HeymacPIeMic


class TestHeyMacIe(unittest.TestCase):
    """Tests the HeymacIE building and serializing."""

    def test_HIeTerm(self):
        ie = HeymacHIeTerm()
        b = bytes(ie)
        self.assertEqual(b, b"\x00")

        c = HeymacIe.parse(b)
        self.assertIs(type(c), HeymacHIeTerm)


    def test_HIeSqncNmbr(self):
        ie = HeymacHIeSqncNmbr(0x2A)
        b = bytes(ie)
        self.assertEqual(b, b"\x81\x00\x2A")

        ie = HeymacIe.parse(b)
        self.assertIs(type(ie), HeymacHIeSqncNmbr)
        self.assertEqual(ie._sqnc_nmbr, 0x2A)


    def test_HIeCipher(self):
        ie = HeymacHIeCipher(0x1234)
        b = bytes(ie)
        self.assertEqual(b, b"\x82\x12\x34")

        ie = HeymacIe.parse(b)
        self.assertIs(type(ie), HeymacHIeCipher)
        self.assertEqual(ie._cipher_info, 0x1234)


    def test_PIeTerm(self):
        ie = HeymacPIeTerm()
        b = bytes(ie)
        self.assertEqual(b, b"\x20")

        c = HeymacIe.parse(b)
        self.assertIs(type(c), HeymacPIeTerm)


    def test_PIeFrag0(self):
        ie = HeymacPIeFrag0(dgram_sz=200, dgram_tag=17)
        b = bytes(ie)
        self.assertEqual(b, b"\xA1\x19\x11")

        ie = HeymacIe.parse(b)
        self.assertIs(type(ie), HeymacPIeFrag0)
        self.assertEqual(ie._dgram_sz, 200)
        self.assertEqual(ie._dgram_tag, 17)


    def test_PIeFragN(self):
        ie = HeymacPIeFragN(dgram_offset=120, dgram_tag=17)
        b = bytes(ie)
        self.assertEqual(b, b"\xA2\x0F\x11")

        ie = HeymacIe.parse(b)
        self.assertIs(type(ie), HeymacPIeFragN)
        self.assertEqual(ie._dgram_offset, 120)
        self.assertEqual(ie._dgram_tag, 17)


    def test_PIeMic(self):
        ie = HeymacPIeMic(mic_algo=5, mic_sz=4)
        b = bytes(ie)
        self.assertEqual(b, b"\xA3\x05\x04")

        ie = HeymacIe.parse(b)
        self.assertIs(type(ie), HeymacPIeMic)
        self.assertEqual(ie._mic_algo, 5)
        self.assertEqual(ie._mic_sz, 4)

    # TODO: unhappy cases
    # with self.assertRaises(HeymacCmdError):
    #     _ = HeymacCmdTxt()


if __name__ == '__main__':
    unittest.main()
