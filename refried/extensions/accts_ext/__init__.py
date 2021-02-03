"""Portfolio list extension for Fava.

This is a simple example of Fava's extension reports system.
"""
import re

from beancount.core.data import iter_entry_dates
from beancount.core.data import Open
from beancount.core.number import Decimal
from beancount.core.number import ZERO
from beancount.core.inventory import Inventory
from beancount.query import query

from fava.core.tree import Tree
from fava.ext import FavaExtensionBase
from fava.template_filters import cost_or_value

from refried import _reverse_parents

import datetime


class AcctsExt(FavaExtensionBase):  # pragma: no cover
    """Sample Extension Report that just prints out an Portfolio List.
    """

    report_title = "Accounts"

    def make_table(self):
        """An account tree based on matching regex patterns."""
        cash = self.ledger.all_root_account.get('Assets')
        credit = self.ledger.all_root_account.get('Liabilities')

        _, wrows = query.run_query(self.ledger.entries, self.ledger.options, '''
            select account,number(only("USD", sum(position)))
                from not "future" in tags
                where account ~ "^(Assets|Liabilities)"
                    and (meta('_cleared') = True or number < 0)
                group by 1''')
        _, crows = query.run_query(self.ledger.entries, self.ledger.options, '''
            select account,number(only("USD", sum(position)))
                from not "future" in tags
                where account ~ "^(Assets|Liabilities)"
                    and (meta('_cleared') = True)
                group by 1''')
        _, trows = query.run_query(self.ledger.entries, self.ledger.options, '''
            select account,number(only("USD", sum(position)))
                from not "future" in tags
                where account ~ "^(Assets|Liabilities)"
                group by 1''')

        self.wrows = dict(wrows)
        self.crows = dict(crows)
        self.trows = dict(trows)

        return [cash, credit]

    def _ordering(self, a):
        def _ordermap(a):
            meta = self.ledger.accounts[a].meta
            return tuple(map(int, str(meta.get('ordering', 999999)).split('.')))
        return tuple(map(_ordermap, _reverse_parents(a.account)))

    def _name(self, a):
        meta = self.ledger.accounts[a.account].meta
        #return meta.get('name', a.account.rsplit(':', 1)[-1])
        return a.account.rsplit(':', 1)[-1]

    def _sort_subtree(self, root):
        children = list(root.values())
        children.sort(key=self._ordering)
        return children

    def _row(self, rows, a):
        d = rows.get(a.account)
        if d is None:
            d = Decimal()
        return d

    def _row_children(self, rows, a):
        sum = Decimal()
        for sub in rows:
            if sub.startswith(a.account):
                sum += rows[sub] if rows[sub] else Decimal()
        return sum

    def _is_open(self, a):
        close_date = self.ledger.accounts[a.account].close_date
        return close_date >= datetime.date.today()
