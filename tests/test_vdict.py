#!/usr/bin/env python3


import time
import unittest

import vdict


class TestValidatedDict(unittest.TestCase):
    """Tests the vdict.ValidatedDict
    """

    def test_happy(self,):
        d = vdict.ValidatedDict()
        d[0] = "zero"
        d[1] = "one"
        self.assertEqual(d[0].value, "zero")
        self.assertEqual(d[0].valid, True)
        self.assertEqual(d[1].value, "one")
        self.assertEqual(d[1].valid, True)

        d.set_expiration(0, 0.1)
        time.sleep(0.2)
        self.assertEqual(d[0].value, "zero")
        self.assertEqual(d[0].valid, False)
        self.assertEqual(d[1].value, "one")
        self.assertEqual(d[1].valid, True)

        d.set_default_expiration(0.1)
        self.assertEqual(d[0].value, "zero")
        self.assertEqual(d[0].valid, False)
        self.assertEqual(d[1].value, "one")
        self.assertEqual(d[1].valid, False)

    def test_str(self,):
        d = vdict.ValidatedDict()
        d[0] = "zero"
        d[1] = "one"
        s = str(d[0])
        self.assertEqual(s, "('zero', True)")


if __name__ == '__main__':
    unittest.main()
