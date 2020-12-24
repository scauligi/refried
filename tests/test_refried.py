import unittest

import refried
from refried import *

from decimal import Decimal

def test_version():
    assert refried.__version__ == '0.4.0'

class TestRefried(unittest.TestCase):
    def test_halfcents(self):
        self.assertEqual(halfcents(Decimal(0)),             '0.00')
        self.assertEqual(halfcents(Decimal(-0)),            '0.00')
        self.assertEqual(halfcents(Decimal(1)),             '1.00')
        self.assertEqual(halfcents(Decimal('.23')),         '0.23')
        self.assertEqual(halfcents(Decimal('2.3')),         '2.30')
        self.assertEqual(halfcents(Decimal('2.345')),       '2.345')
        self.assertEqual(halfcents(Decimal('-2.3')),       '-2.30')
        self.assertEqual(halfcents(Decimal('-2.345')),     '-2.345')
        self.assertEqual(halfcents(Decimal('2932.34')), '2,932.34')
