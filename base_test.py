from unittest import TestCase


class BaseTest(TestCase):
    def assertBetween(self, lo, hi, x):
        if not (lo <= x <= hi):
            raise AssertionError('%r not between %r and %r' % (x, lo, hi))
