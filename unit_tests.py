import unittest
import client_main
import math


class TestRateTrackers(unittest.TestCase):
    def check_same_result(self, values):
        a = client_main.RateTrackerSimple()
        b = client_main.RateTrackerRolling()
        for v in values:
            a._add(v)
            b._add(v)

        a_res = a.stats()
        b_res = b.stats()
        for a_val, b_val in zip(a_res, b_res):
            # different method of calculation may result in slightly different result due to floating point issues
            self.assertAlmostEqual(a_val, b_val)

    def test_simple(self):
        self.check_same_result([1, 2, 3])

    def test_harder(self):
        self.check_same_result([1.1, 2.2, 3.3, 4.4, math.pi, math.e, 42])


if __name__ == '__main__':
    unittest.main()