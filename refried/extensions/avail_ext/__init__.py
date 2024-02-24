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

import refried
from refried import filter_postings, _reverse_parents, Period

import datetime
from collections import defaultdict as ddict


class AvailExt(FavaExtensionBase):  # pragma: no cover
    report_title = "Budget"

    def make_table(self, period):
        """An account tree based on matching regex patterns."""
        today = datetime.date.today()

        if period is not None:
            period = Period.from_str(period)
        else:
            period = Period.from_date(today)

        self.account_types = refried.get_account_types(self.ledger.options)
        self.open_close_map = getters.get_account_open_close(self.ledger.all_entries)

        self.tree = {}
        def slurp(tree):
            for k, (_, v) in list(tree.items()):
                self.tree[k] = v
                slurp(v)
        slurp(refried.tree(self.open_close_map, start=period))
        root = [
            self.account_types.income,
            self.account_types.expenses,
        ]


        # self.period_start = self.ledger._date_first
        # self.period_end = self.ledger._date_last
        self.period_start = period.asdate()
        self.period_end = period.add(1).asdate()

        endtoday = self.period_end
        if Period.from_date(today) == period:
            endtoday = today + datetime.timedelta(days=1)

        self.brows = ddict(Inventory)
        self.midbrows = ddict(Inventory)
        self.srows = ddict(Inventory)
        self.midsrows = ddict(Inventory)
        self.vrows = ddict(Inventory)
        self.midvrows = ddict(Inventory)
        for entry, posting in filter_postings(self.ledger.all_entries):
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

        return root, str(period)

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
        return "{} {}".format(num, currency)

    def _ordering(self, a):
        def _ordermap(a):
            meta = self.ledger.accounts[a].meta
            return tuple(map(int, str(meta.get('ordering', 999999)).split('.')))
        return tuple(map(_ordermap, _reverse_parents(a.account)))

    def _name(self, a):
        meta = self.ledger.accounts[a].meta
        return meta.get('name', a)

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

    def _many_positions(self, inventory):
        if inventory is None:
            return []
        inventory = inventory.reduce(convert.get_weight)
        if inventory.is_empty():
            return []
        return [pos.units for pos in inventory.get_positions()]

    def _row(self, rows, a):
        d: Inventory = rows.get(a)
        return [-amt for amt in self._many_positions(d)]

    def _row_children(self, rows, a):
        sum = Inventory()
        for sub in rows:
            if sub.startswith(a):
                sum.add_inventory(rows.get(sub, Inventory()))
        amts = [-amt for amt in self._many_positions(sum.reduce(convert.get_weight))]
        return amts if amts else [Amount(ZERO, "USD")]

    def _has_children(self, a):
        # return sum(self._is_open(c) for c in a.values())
        return bool(self.tree[a])

    def _children(self, a):
        return list(self.tree[a].keys())

    def _is_open(self, a):
        if not a:
            return False
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
