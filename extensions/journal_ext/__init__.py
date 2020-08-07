"""Portfolio list extension for Fava.

This is a simple example of Fava's extension reports system.
"""
import re

from beancount.core.compare import hash_entry
from beancount.core.data import iter_entry_dates
from beancount.core.data import Open, Transaction
from beancount.core.number import Decimal
from beancount.core.number import ZERO
from beancount.core.inventory import Inventory
from beancount.query import query

from fava.core.tree import Tree
from fava.ext import FavaExtensionBase
from fava.template_filters import cost_or_value

import datetime
import re


class JournalExt(FavaExtensionBase):  # pragma: no cover
    """Sample Extension Report that just prints out an Portfolio List.
    """

    report_title = "Journal"

    def _wct(self, account_name):
        if not account_name:
            account_name = '^(Assets:|Liabilities:)'
        _, wrow = query.run_query(self.ledger.entries, self.ledger.options, '''
            select number(only("USD", sum(position)))
                where account = "{}"
                    and (meta('_cleared') = True or number < 0)
                ''', account_name)
        if not wrow:
            wrow = [[Decimal()]]
        _, crow = query.run_query(self.ledger.entries, self.ledger.options, '''
            select number(only("USD", sum(position)))
                where account = "{}"
                    and (meta('_cleared') = True)
                ''', account_name)
        if not crow:
            crow = [[Decimal()]]
        _, trow = query.run_query(self.ledger.entries, self.ledger.options, '''
            select number(only("USD", sum(position)))
                where account = "{}"
                ''', account_name)
        if not trow:
            trow = [[Decimal()]]
        return wrow[0][0], crow[0][0], trow[0][0]

    def _get_entries(self, account_name):
        wjc = self.ledger.fava_options['account-journal-include-children']
        if account_name:
            entries = self.ledger.account_journal(
                account_name,
                with_journal_children=wjc)
        else:
            entries = self.ledger.account_journal(
                'Assets',
                with_journal_children=wjc)
            entries += self.ledger.account_journal(
                'Liabilities',
                with_journal_children=wjc)
        return entries

    @staticmethod
    def _flag_for_account(entry, account_name):
        flag = None
        flagtype = ''
        if isinstance(entry, Transaction):
            flag = entry.flag
            if entry.flag != '*':
                flagtype = 'pending' if flag == '!' else 'other'
            else:
                flagtype = 'cleared'
                for posting in filter(lambda p: (not account_name) or p.account == account_name, entry.postings):
                    if not posting.meta or not posting.meta.get('_cleared', False):
                        flagtype = 'pending'
        return flag, flagtype

    @staticmethod
    def _flag_for_posting(posting):
        flag = posting.flag
        flagtype = 'normal'
        if JournalExt._is_account_account(posting.account) \
                and (not flag or flag == '*') \
                and posting.meta \
                and not posting.meta.get('_cleared', False):
            flagtype = 'pending'
        elif flag == '!':
            flagtype = 'pending'
        elif flag:
            flagtype = 'other'
        return flag, flagtype

    @staticmethod
    def _is_expense_account(account_name):
        return account_name.startswith('Expenses:') or account_name.startswith('Income:')

    @staticmethod
    def _is_account_account(account_name):
        return account_name.startswith('Assets:') or account_name.startswith('Liabilities:')

    def _get_target(self, entry, account_name):
        if isinstance(entry, Transaction):
            expenses = set()
            accounts = set()
            for posting in entry.postings:
                if account_name != posting.account:
                    if self._is_expense_account(posting.account):
                        expenses.add(posting.account)
                    elif self._is_account_account(posting.account):
                        accounts.add(posting.account)
            if len(expenses) == 1:
                acct ,= expenses
                name = self._name(acct)
                if accounts:
                    name = f'({name})'
                return (acct, name)
            elif not expenses and len(accounts) == 1:
                acct ,= accounts
                name = self._name(acct)
                return (acct, name)
        return ('', '')

    def _name(self, a):
        meta = self.ledger.accounts[a].meta
        return meta.get('name', a)

    @staticmethod
    def _hash_entry(entry):
        return 'entry-' + hash_entry(entry)

    def _toggleDate(self, account_name, entry_hash):
        _, _, slice_, sha256sum = self.ledger.context(entry_hash)
        lines = slice_.split('\n')
        i = 1
        while i < len(lines):
            line = lines[i]
            if re.match(rf'\s+{account_name}', line):
                i += 1
                addDate = True
                while i < len(lines):
                    line = lines[i]
                    if re.match(r'\s+date:\s*$', line):
                        # found empty date: -- remove it
                        lines.pop(i)
                        i -= 1  # since we just removed a line
                        addDate = False
                        break
                    elif re.match(r'\s+date:\s*.$', line):
                        # found non-empty date: -- do nothing
                        addDate = False
                        break
                    elif re.match(r'\s+[A-Z]', line):
                        # found no date: meta
                        break
                    i += 1
                if addDate:
                    lines.insert(i, '    date:')
            i += 1
        new_slice = '\n'.join(lines)
        self.ledger.file.save_entry_slice(entry_hash, new_slice, sha256sum)
