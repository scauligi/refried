import unittest
import datetime
from __init__ import Period

class TestPeriod(unittest.TestCase):
    def test_add0(self):
        p = Period(2020, 1)
        self.assertEqual(p, p.add(0))
        p = Period(2020, 2)
        self.assertEqual(p, p.add(0))
        p = Period(2020, 11)
        self.assertEqual(p, p.add(0))
        p = Period(2020, 12)
        self.assertEqual(p, p.add(0))

    def test_add1(self):
        p1 = Period(2020, 1)
        p2 = Period(2020, 2)
        p3 = Period(2020, 3)
        p11 = Period(2020, 11)
        p12 = Period(2020, 12)
        p13 = Period(2021, 1)
        self.assertEqual(p1.add(1), p2)
        self.assertEqual(p2.add(1), p3)
        self.assertEqual(p11.add(1), p12)
        self.assertEqual(p12.add(1), p13)
        self.assertEqual(p1, p2.sub(1))
        self.assertEqual(p2, p3.sub(1))
        self.assertEqual(p11, p12.sub(1))
        self.assertEqual(p12, p13.sub(1))

    def test_add4(self):
        p1 = Period(2020, 1)
        p2 = Period(2020, 2)
        p5 = Period(2020, 5)
        p6 = Period(2020, 6)
        p8 = Period(2020, 8)
        p9 = Period(2020, 9)
        p10 = Period(2020, 10)
        p12 = Period(2020, 12)
        p13 = Period(2021, 1)
        p14 = Period(2021, 2)
        self.assertEqual(p1.add(4), p5)
        self.assertEqual(p2.add(4), p6)
        self.assertEqual(p8.add(4), p12)
        self.assertEqual(p9.add(4), p13)
        self.assertEqual(p10.add(4), p14)

    def test_asdate(self):
        p = Period(2020, 5)
        self.assertEqual(p.asdate(), datetime.date(2020, 5, 1))

if __name__ == '__main__':
    unittest.main()
