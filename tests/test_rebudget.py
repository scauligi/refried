import unittest

from beancount.parser import cmptest
from beancount import loader

import refried

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

    @loader.load_doc(expect_errors=True)
    def test_tracking_mismatch(self, entries, errors, options):
        """
            plugin "refried.plugins.rebudget"

            2020-09-21 open Assets:Cash
            2020-09-21 open Assets:IRA
                tracking: TRUE

            2020-09-21 *
                Assets:Cash    -20 USD
                Assets:IRA      20 USD
        """
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], refried.plugins.rebudget.BudgetBalanceError)

    @loader.load_doc(expect_errors=False)
    def test_tracking_ok(self, entries, errors, options):
        """
            plugin "refried.plugins.rebudget"

            2020-09-21 open Assets:Cash
            2020-09-21 open Assets:IRA
                tracking: TRUE
            2020-09-21 open Expenses:Money-for-IRA
            2020-09-21 open Income:Tracking
                tracking: TRUE

            2020-09-21 *
                Assets:Cash       -20 USD
                Assets:IRA         20 USD

            2020-09-21 *
                Income:Tracking         -20 USD
                Expenses:Money-for-IRA   20 USD
        """
        pass


    # Tests with different root account names

    @loader.load_doc(expect_errors=False)
    def test_leave_alone_with_other_roots(self, entries, errors, options):
        """
            plugin "refried.plugins.rebudget"

            option "name_assets" "Activos"
            option "name_liabilities" "Pasivos"
            option "name_equity" "Capital"
            option "name_income" "Ingresos"
            option "name_expenses" "Gastos"

            2020-05-28 open Activos:Corriente
            2020-05-28 open Pasivos:Credito

            2020-05-28 *
                Activos:Corriente      -20 USD
                Pasivos:Credito         20 USD
        """
        self.assertEqualEntries(self.test_leave_alone_with_other_roots.__input__, entries)

    @loader.load_doc(expect_errors=False)
    def test_expense_expense_with_other_roots(self, entries, errors, options):
        """
            plugin "refried.plugins.rebudget"

            option "name_assets" "Activos"
            option "name_liabilities" "Pasivos"
            option "name_equity" "Capital"
            option "name_income" "Ingresos"
            option "name_expenses" "Gastos"

            2020-05-28 open Gastos:Dining-Out
            2020-05-28 open Gastos:Groceries

            2020-05-28 *
                Gastos:Dining-Out   -20 USD
                Gastos:Groceries     20 USD
        """
        self.assertEqualEntries("""
            plugin "refried.plugins.rebudget"

            option "name_assets" "Activos"
            option "name_liabilities" "Pasivos"
            option "name_equity" "Capital"
            option "name_income" "Ingresos"
            option "name_expenses" "Gastos"

            2020-05-28 open Gastos:Dining-Out
            2020-05-28 open Gastos:Groceries

            2020-05-28 * #rebudget
                Gastos:Dining-Out   -20 USD
                Gastos:Groceries     20 USD
        """, entries)

