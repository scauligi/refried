import unittest

from beancount.parser import cmptest
from beancount import loader
from beancount.utils import test_utils

from . import test_utils

class TestEvensplit(test_utils.TestCase):

    @loader.load_doc(expect_errors=False)
    def test_split(self, entries, errors, options):
        """
            plugin "refried.plugins.evensplit"

            2020-05-28 open Assets:Cash
            2020-05-28 open Liabilities:Partner
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                Expenses:Dining-Out    20 USD
                    split: Liabilities:Partner
        """
        self.assertEqualEntries("""
            2020-05-28 open Assets:Cash
            2020-05-28 open Liabilities:Partner
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                Liabilities:Partner    10 USD
                Expenses:Dining-Out    10 USD
        """, entries)

    @loader.load_doc(expect_errors=False)
    def test_with_interpolation(self, entries, errors, options):
        """
            plugin "refried.plugins.evensplit"

            2020-05-28 open Assets:Cash
            2020-05-28 open Liabilities:Partner
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                Expenses:Dining-Out
                    split: Liabilities:Partner
        """
        self.assertEqualEntries("""
            2020-05-28 open Assets:Cash
            2020-05-28 open Liabilities:Partner
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                Liabilities:Partner    10 USD
                Expenses:Dining-Out    10 USD
        """, entries)

    @loader.load_doc(expect_errors=False)
    def test_with_meta(self, entries, errors, options):
        """
            plugin "refried.plugins.evensplit"

            2020-05-28 open Assets:Cash
            2020-05-28 open Liabilities:Partner
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                Expenses:Dining-Out
                    meta: "data"
                    split: Liabilities:Partner
        """
        self.assertEqualEntries("""
            2020-05-28 open Assets:Cash
            2020-05-28 open Liabilities:Partner
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                Liabilities:Partner    10 USD
                    meta: "data"
                Expenses:Dining-Out    10 USD
                    meta: "data"
        """, entries)

    @loader.load_doc(expect_errors=False)
    def test_with_meta_sanity(self, entries, errors, options):
        """
            plugin "refried.plugins.evensplit"

            2020-05-28 open Assets:Cash
            2020-05-28 open Liabilities:Partner
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                Expenses:Dining-Out
                    meta: "data"
                    split: Liabilities:Partner
        """
        with self.assertRaises(AssertionError):
            self.assertEqualEntries("""
                2020-05-28 open Assets:Cash
                2020-05-28 open Liabilities:Partner
                2020-05-28 open Expenses:Dining-Out

                2020-05-28 *
                    Assets:Cash           -20 USD
                    Liabilities:Partner    10 USD
                    Expenses:Dining-Out    10 USD
                        meta: "data"
            """, entries)

if __name__ == '__main__':
    unittest.main()
