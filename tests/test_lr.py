#!/usr/bin/env python3


import unittest

import mth_lr


class TestLinearRegression(unittest.TestCase):
    """Tests the mth_lr.LinearRegression
    """

    def test_happy(self,):
        """Test values come from "Why all the math?", Jack Crenshaw, embedded.com, 2009/06/05
        """
        linreg = mth_lr.LinearRegression(4)

        linreg.update(0, 1.23)
        linreg.update(1, 1.51)
        linreg.update(2, 1.88)
        linreg.update(3, 2.60)

        self.assertAlmostEqual(linreg.get_est(0), 1.133)
        self.assertAlmostEqual(linreg.get_est(5), 3.373)


if __name__ == '__main__':
    unittest.main()
