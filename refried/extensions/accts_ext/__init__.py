from beancount.core import realization
from beancount.core.data import Balance
from beancount.core.number import Decimal, ZERO
from beancount.core.inventory import Inventory, Amount
from beancount.query import query

from fava.ext import FavaExtensionBase

from refried import _reverse_parents

import refried
from beancount.core import account as acctops
from refried import get_account_types, is_account_type
from collections import defaultdict as ddict
from fava.core.inventory import CounterInventory
from dataclasses import dataclass, field

import datetime


@dataclass
class Acct:
    has_balance: bool = False
    working: CounterInventory = field(default_factory=CounterInventory)
    cleared: CounterInventory = field(default_factory=CounterInventory)
    total: CounterInventory = field(default_factory=CounterInventory)
    children: "Acct" = field(default_factory=lambda: Acct(children=None))

    def add_posting(self, posting):
        self.has_balance = True
        self.total.add_position(posting)
        if posting.meta.get('_cleared', False):
            self.working.add_position(posting)
            self.cleared.add_position(posting)
        elif posting.units.number < 0:
            self.working.add_position(posting)

class AcctsExt(FavaExtensionBase):
    report_title = "Accounts"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.open_close = refried.get_account_entries(self.ledger.all_entries)
        last_date = self.ledger.all_entries[-1].date
        self._tree = refried.tree(self.open_close, last_date)

    def make_table2(self):
        account_types = get_account_types(self.ledger.options)
        is_account_account = lambda a: is_account_type((account_types.assets, account_types.liabilities), a)

        table = ddict(Acct)

        for tx in self.ledger.all_entries_by_type.Transaction:
            if "future" in tx.tags:
                continue
            for posting in tx.postings:
                if is_account_account(posting.account):
                    table[posting.account].add_posting(posting)
                    for account in acctops.parents(posting.account):
                        table[account].children.add_posting(posting)

        return table

    def tree(self, root):
        return self._tree[root]

    def aname(self, account_name):
        return refried.aname(self.open_close, account_name)

    def show_if_zero(self, amounts):
        amounts = list(amounts)
        if amounts:
            return amounts
        return [Amount(Decimal(), self.ledger.options['operating_currency'][0])]

    def make_table(self):
        """An account tree based on matching regex patterns."""
        cash = self.ledger.accounts.get('Assets')
        credit = self.ledger.accounts.get('Liabilities')

        _, wrows = query.run_query(self.ledger.all_entries, self.ledger.options, '''
            select account,sum(position)
                from not "future" in tags
                where account ~ "^(Assets|Liabilities)"
                    and (meta('_cleared') = True or number < 0)
                group by 1''')
        _, crows = query.run_query(self.ledger.all_entries, self.ledger.options, '''
            select account,sum(position)
                from not "future" in tags
                where account ~ "^(Assets|Liabilities)"
                    and (meta('_cleared') = True)
                group by 1''')
        _, trows = query.run_query(self.ledger.all_entries, self.ledger.options, '''
            select account,sum(position)
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
        name = meta.get('name')
        if name is None:
            name = a.account.rsplit(':', 1)[-1]
        return name

    def _sort_subtree(self, root):
        children = list(root.values())
        children.sort(key=self._ordering)
        return children

    def _row(self, rows, a):
        inv = rows.get(a.account, Inventory())
        return [pos.units for pos in inv.get_positions()]

    def _row_children(self, rows, a):
        sum = Inventory()
        for sub in rows:
            if sub.startswith(a.account) and not rows[sub].is_empty():
                sum += rows[sub]
        return [pos.units for pos in sum.get_positions()] if not sum.is_empty() else [Amount(ZERO, "USD")]

    def _is_open(self, a):
        if not a:
            return True
        acct = self.ledger.accounts[a.account]
        if acct:
            close_date = self.ledger.accounts[a.account].close_date
            return close_date >= datetime.date.today()
        return True

    def account_uptodate_status(self, account_name):
        """Status of the last balance.

        Args:
            account_name: An account name.

        Returns:
            A status string for the last balance of the account,
            as well as the date of the last balance.

            - 'green':  A balance check that passed.
            - 'red':    A balance check that failed.
        """

        status = None
        date = None
        for txn_posting in reversed(self.ledger.all_entries_by_type.Balance):
            if txn_posting.account == account_name:
                date = txn_posting.date
                if txn_posting.diff_amount:
                    status = "red"
                    break
                # XXX check date
                status = "green"
                break

        return status, date
