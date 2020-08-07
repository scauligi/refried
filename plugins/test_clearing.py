import unittest

from beancount.core.data import Transaction
from beancount.parser import cmptest
from beancount import loader

import test_utils

import sys
from os.path import dirname, realpath
sys.path.insert(0, dirname(dirname(dirname(realpath(sys.argv[0])))))

def _underscore_cleared_posting(p):
    if 'cleared' in p.meta:
        p.meta['_cleared'] = p.meta['cleared']
        del p.meta['cleared']
    return p

def _underscore_cleared_entry(e):
    if isinstance(e, Transaction):
        e = e._replace(postings=list(map(_underscore_cleared_posting, e.postings)))
    return e

def _underscore_cleared(entries_or_str):
    entries = cmptest.read_string_or_entries(entries_or_str)
    return list(map(_underscore_cleared_entry, entries))

class TestClearing(test_utils.TestCase):

    @loader.load_doc(expect_errors=False)
    def test_leave_alone(self, entries, errors, options):
        """
            plugin "refried.plugins.clearing"

            2020-05-28 open Expenses:Dining-Out
            2020-05-28 open Income:Salary

            2020-05-28 *
                Income:Salary         -20 USD
                Expenses:Dining-Out    20 USD
        """
        self.assertEqualEntries(self.test_leave_alone.__input__, entries)

    @loader.load_doc(expect_errors=False)
    def test_uncleared(self, entries, errors, options):
        """
            plugin "refried.plugins.clearing"

            2020-05-28 open Assets:Cash
            2020-05-28 open Liabilities:Credit
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                Liabilities:Credit     20 USD

            2020-05-28 *
                Assets:Cash           -20 USD
                Expenses:Dining-Out    20 USD

            2020-05-29 *
                Assets:Cash           -20 USD
                    uncleared:
                Expenses:Dining-Out    20 USD
        """
        expected = _underscore_cleared("""
            plugin "refried.plugins.clearing"

            2020-05-28 open Assets:Cash
            2020-05-28 open Liabilities:Credit
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                    cleared: FALSE
                Liabilities:Credit     20 USD
                    cleared: FALSE

            2020-05-28 *
                Assets:Cash           -20 USD
                    cleared: FALSE
                Expenses:Dining-Out    20 USD

            2020-05-29 *
                Assets:Cash           -20 USD
                    cleared: FALSE
                Expenses:Dining-Out    20 USD
        """)
        self.assertEqualEntries(expected, entries)

    @loader.load_doc(expect_errors=False)
    def test_autoclear(self, entries, errors, options):
        """
            plugin "refried.plugins.clearing"

            2020-05-28 open Assets:Cash
                autoclear: TRUE
            2020-05-28 open Liabilities:Credit
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                Liabilities:Credit     20 USD

            2020-05-28 *
                Assets:Cash           -20 USD
                Expenses:Dining-Out    20 USD

            2020-05-29 *
                Assets:Cash           -20 USD
                    uncleared:
                Expenses:Dining-Out    20 USD
        """
        expected = _underscore_cleared("""
            plugin "refried.plugins.clearing"

            2020-05-28 open Assets:Cash
                autoclear: TRUE
            2020-05-28 open Liabilities:Credit
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                    cleared: TRUE
                Liabilities:Credit     20 USD
                    cleared: FALSE

            2020-05-28 *
                Assets:Cash           -20 USD
                    cleared: TRUE
                Expenses:Dining-Out    20 USD

            2020-05-29 *
                Assets:Cash           -20 USD
                    cleared: FALSE
                Expenses:Dining-Out    20 USD
        """)
        self.assertEqualEntries(expected, entries)

    @loader.load_doc(expect_errors=False)
    def test_cleared_before(self, entries, errors, options):
        """
            plugin "refried.plugins.clearing"

            2020-05-28 open Assets:Cash
                cleared_before: 2020-06-01
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                Expenses:Dining-Out    20 USD

            2020-05-29 *
                Assets:Cash           -20 USD
                    uncleared:
                Expenses:Dining-Out    20 USD

            2020-06-01 *
                Assets:Cash           -20 USD
                Expenses:Dining-Out    20 USD

            2020-06-02 *
                Assets:Cash           -20 USD
                Expenses:Dining-Out    20 USD
        """
        expected = _underscore_cleared("""
            plugin "refried.plugins.clearing"

            2020-05-28 open Assets:Cash
                cleared_before: 2020-06-01
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                    cleared: TRUE
                Expenses:Dining-Out    20 USD

            2020-05-29 *
                Assets:Cash           -20 USD
                    cleared: FALSE
                Expenses:Dining-Out    20 USD

            2020-06-01 *
                Assets:Cash           -20 USD
                    cleared: FALSE
                Expenses:Dining-Out    20 USD

            2020-06-02 *
                Assets:Cash           -20 USD
                    cleared: FALSE
                Expenses:Dining-Out    20 USD
        """)
        self.assertEqualEntries(expected, entries)

    @loader.load_doc(expect_errors=False)
    def test_date(self, entries, errors, options):
        """
            plugin "refried.plugins.clearing"

            2020-05-28 open Assets:Cash
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                    date:
                Expenses:Dining-Out    20 USD

            2020-05-29 *
                Assets:Cash           -20 USD
                    date:
                    uncleared:
                Expenses:Dining-Out    20 USD
        """
        expected = _underscore_cleared("""
            plugin "refried.plugins.clearing"

            2020-05-28 open Assets:Cash
            2020-05-28 open Expenses:Dining-Out

            2020-05-28 *
                Assets:Cash           -20 USD
                    cleared: TRUE
                    date:
                Expenses:Dining-Out    20 USD

            2020-05-29 *
                Assets:Cash           -20 USD
                    cleared: FALSE
                    date:
                Expenses:Dining-Out    20 USD
        """)
        self.assertEqualEntries(expected, entries)

if __name__ == '__main__':
    unittest.main()
