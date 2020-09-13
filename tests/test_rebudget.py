import unittest

from beancount.parser import cmptest
from beancount import loader

class TestRebudget(cmptest.TestCase):

    @loader.load_doc(expect_errors=False)
    def test_leave_alone(self, entries, errors, options):
        """
            plugin "refried.plugins.rebudget"

            2020-05-28 open Assets:Cash
            2020-05-28 open Liabilities:Credit

            2020-05-28 *
                Assets:Cash           -20 USD
                Liabilities:Credit     20 USD
        """
        self.assertEqualEntries(self.test_leave_alone.__input__, entries)

    @loader.load_doc(expect_errors=False)
    def test_expense_expense(self, entries, errors, options):
        """
            plugin "refried.plugins.rebudget"

            2020-05-28 open Expenses:Dining-Out
            2020-05-28 open Expenses:Groceries

            2020-05-28 *
                Expenses:Dining-Out   -20 USD
                Expenses:Groceries     20 USD
        """
        self.assertEqualEntries("""
            plugin "refried.plugins.rebudget"

            2020-05-28 open Expenses:Dining-Out
            2020-05-28 open Expenses:Groceries

            2020-05-28 * #rebudget
                Expenses:Dining-Out   -20 USD
                Expenses:Groceries     20 USD
        """, entries)

    @loader.load_doc(expect_errors=False)
    def test_existing_tag(self, entries, errors, options):
        """
            plugin "refried.plugins.rebudget"

            2020-05-28 open Expenses:Dining-Out
            2020-05-28 open Expenses:Groceries

            2020-05-28 * #tagged
                Expenses:Dining-Out   -20 USD
                Expenses:Groceries     20 USD
        """
        self.assertEqualEntries("""
            plugin "refried.plugins.rebudget"

            2020-05-28 open Expenses:Dining-Out
            2020-05-28 open Expenses:Groceries

            2020-05-28 * #tagged #rebudget
                Expenses:Dining-Out   -20 USD
                Expenses:Groceries     20 USD
        """, entries)

    @loader.load_doc(expect_errors=False)
    def test_expense_income(self, entries, errors, options):
        """
            plugin "refried.plugins.rebudget"

            2020-05-28 open Expenses:Dining-Out
            2020-05-28 open Income:Salary

            2020-05-28 *
                Expenses:Dining-Out   -20 USD
                Income:Salary          20 USD
        """
        self.assertEqualEntries("""
            plugin "refried.plugins.rebudget"

            2020-05-28 open Expenses:Dining-Out
            2020-05-28 open Income:Salary

            2020-05-28 * #rebudget
                Expenses:Dining-Out   -20 USD
                Income:Salary          20 USD
        """, entries)

    @loader.load_doc(expect_errors=True)
    def test_expense_equity(self, entries, errors, options):
        """
            plugin "refried.plugins.rebudget"

            2020-05-28 open Expenses:Dining-Out
            2020-05-28 open Equity:Something

            2020-05-28 *
                Expenses:Dining-Out   -20 USD
                Equity:Something       20 USD
        """
        self.assertEqualEntries("""
            plugin "refried.plugins.rebudget"

            2020-05-28 open Expenses:Dining-Out
            2020-05-28 open Equity:Something

            2020-05-28 * #rebudget
                Expenses:Dining-Out   -20 USD
                Equity:Something       20 USD
        """, entries)
