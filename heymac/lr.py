"""
Copyright 2018 Dean Hall.  See LICENSE for details.

A class to perform Linear Regression for y = f(x) = a + b * x
"""


class LinearRegression(object):
    def __init__(self, depth):
        """Create an instance with the given queue depth.
        """
        self.n = 0
        self.depth = depth

        # Circular queues init'd proper depth with all zeroes
        self.xi = [0,] * depth
        self.yi = [0,] * depth
        self.xxi = [0,] * depth
        self.xyi = [0,] * depth

        # Sum of each circular queue init'd
        self.sumx = 0
        self.sumy = 0
        self.sumxx = 0
        self.sumxy = 0


    def update(self, x, y):
        """Update the LR with the data point xi, yi
        """
        # Increment the count of data points
        self.n += 1

        xx = x*x
        xy = x*y

        # Add the data to the circular queues
        self.xi.insert(0, x)
        self.yi.insert(0, y)
        self.xxi.insert(0, xx)
        self.xyi.insert(0, xy)

        # Remove the oldest data from the circular queue.
        # Add the new data and subtract the oldest data
        # from the running sums.
        self.sumx += x - self.xi.pop()
        self.sumy += y - self.yi.pop()
        self.sumxx += xx - self.xxi.pop()
        self.sumxy += xy - self.xyi.pop()


    def get_est(self, x):
        """Returns an estimate of f(x) for the given input, x.
        Returns None if no data points have been fed to the update() method.
        """
        if self.n == 0:
            return None
        elif self.n > self.depth:
            n = self.depth
        else:
            n = self.n

        sqr_sumx = self.sumx * self.sumx
        inv_det = 1.0 / (n * self.sumxx - sqr_sumx)

        a = inv_det * (self.sumxx * self.sumy - self.sumx * self.sumxy)
        b = inv_det * (-self.sumx * self.sumy + n * self.sumxy)

        return a + b * x


def test():
    """Test values come from "Why all the math?", Jack Crenshaw, embedded.com, 2009/06/05
    """
    import math

    lr = LinearRegression(4)

    lr.update(0, 1.23)
    lr.update(1, 1.51)
    lr.update(2, 1.88)
    lr.update(3, 2.60)

    assert math.isclose(lr.get_est(0), 1.133)
    assert math.isclose(lr.get_est(5), 3.373)


if __name__ == '__main__':
    test()
