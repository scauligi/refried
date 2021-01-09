"""Portfolio list extension for Fava.

This is a simple example of Fava's extension reports system.
"""
import re

from beancount.core import convert
from beancount.core.data import Open
from beancount.core.number import Decimal, ZERO
from beancount.core.inventory import Inventory, Position, Amount
from beancount.core.realization import RealAccount
from beancount.core import getters
from beancount.core import convert
from beancount.query import query

from fava.core.tree import Tree
from fava.ext import FavaExtensionBase
from fava.template_filters import cost_or_value

from refried import filter_postings, _reverse_parents

import datetime
from collections import defaultdict as ddict


class AvailExt(FavaExtensionBase):  # pragma: no cover
    """Sample Extension Report that just prints out an Portfolio List.
    """

    report_title = "Budget"

    def make_table(self, period):
        """An account tree based on matching regex patterns."""
        root = [
            self.ledger.all_root_account.get('Income'),
            self.ledger.all_root_account.get('Expenses'),
        ]

        today = datetime.date.today()

        if period is not None:
            year, month = (int(n) for n in period.split('-', 1))
        else:
            year = today.year
            month = today.month
            period = f'{year:04}-{month:02}'

        self.open_close_map = getters.get_account_open_close(self.ledger.all_entries)

        # self.period_start = self.ledger._date_first
        # self.period_end = self.ledger._date_last
        self.period_start = datetime.date(year, month, 1)
        self.period_end = datetime.date(year+month//12, month%12+1, 1)

        endtoday = self.period_end
        if today.year == self.period_start.year and today.month == self.period_start.month:
            endtoday = today + datetime.timedelta(days=1)

        self.brows = ddict(Inventory)
        self.midbrows = ddict(Inventory)
        self.srows = ddict(Inventory)
        self.midsrows = ddict(Inventory)
        self.vrows = ddict(Inventory)
        self.midvrows = ddict(Inventory)
        for entry, posting in filter_postings(self.ledger.entries):
            if entry.date >= self.period_end:
                continue
            self.vrows[posting.account].add_position(posting)
            if entry.date < endtoday:
                self.midvrows[posting.account].add_position(posting)
            if entry.date < self.period_start:
                continue
            if 'rebudget' in entry.tags:
                rows = self.brows
                midrows = self.midbrows
            else:
                rows = self.srows
                midrows = self.midsrows
            rows[posting.account].add_position(posting)
            if entry.date < endtoday:
                midrows[posting.account].add_position(posting)

        return root, period

    def format_currency(self, value, currency = None, show_if_zero = False):
        if not value and not show_if_zero:
            return ""
        if value == ZERO:
            return self.ledger.format_decimal(ZERO, currency)
        return self.ledger.format_decimal(value, currency)

    def format_amount(self, amount, show_if_zero=False):
        if amount is None:
            return ""
        number, currency = amount
        if number is None:
            return ""
        if currency == "USD":
            return self.format_currency(number, currency, show_if_zero)
        num = self.format_currency(number, currency, show_if_zero=True).replace('\xa0', '')
        return "{} {}\xa0".format(num, currency)

    def _ordering(self, a):
        def _ordermap(a):
            meta = self.ledger.accounts[a].meta
            return tuple(map(int, str(meta.get('ordering', 999999)).split('.')))
        return tuple(map(_ordermap, _reverse_parents(a.account)))

    def _name(self, a):
        meta = self.ledger.accounts[a.account].meta
        return meta.get('name', a.account)

    def _sort_subtree(self, root):
        children = list(root.values())
        children.sort(key=self._ordering)
        return children

    def _only_position(self, inventory):
        if inventory is None:
            return Amount(ZERO, "USD")
        inventory = inventory.reduce(convert.get_weight)
        if inventory.is_empty():
            return Amount(ZERO, "USD")
        return inventory.get_only_position().units

    def _row(self, rows, a):
        if isinstance(a, RealAccount):
            a = a.account
        d: Inventory = rows.get(a)
        return -self._only_position(d)

    def _row_children(self, rows, a):
        sum = Inventory()
        for sub in rows:
            if sub.startswith(a.account):
                sum.add_inventory(rows.get(sub, Inventory()))
        return -self._only_position(sum.reduce(convert.get_weight))

    def _has_children(self, a):
        return sum(self._is_open(c) for c in a.values())

    def _is_open(self, a):
        open, close = self.open_close_map.get(a.account, (None, None))
        return (open is None or open.date < self.period_end) and (close is None or close.date > self.period_start)

    def _period_for(self, date):
        return date.strftime('%Y-%m')

    def _prev_month(self):
        return self._period_for(self.period_start - datetime.timedelta(days=1))

    def _next_month(self):
        return self._period_for(self.period_end)

    def _date_range(self):
        end = self.period_end
        start = self.period_start
        if start.day == 1 and end.day == 1 and (end - start).days in range(28, 32):
            return start.strftime('%b %Y')
        return f'{start} - {end}'
