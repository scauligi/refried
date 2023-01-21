import collections
from refried import is_account_account
from beancount.core import convert, interpolate
from beancount.core.account_types import get_account_type
from beancount.core.data import Open, Transaction, filter_txns
from beancount.core.inventory import Inventory
from beancount.parser.options import get_account_types

__plugins__ = ('rebudget', 'balance_check')

BudgetBalanceError = collections.namedtuple('BudgetBalanceError', 'source message entry')

def rebudget_entry(entry, options_map):
    if isinstance(entry, Transaction):
        for posting in entry.postings:
            if is_account_account(posting.account, options_map):
                break
        else:
            if 'tx' not in entry.tags:
                return entry._replace(tags=(entry.tags | frozenset(('rebudget',))))
    return entry

def rebudget(entries, options_map):
    return [rebudget_entry(e, options_map) for e in entries], []

def balance_check(entries, options_map):
    errors = []
    tracking_accounts = set()
    for entry in entries:
        if isinstance(entry, Open):
            if entry.meta.get('tracking', False):
                tracking_accounts.add(entry.account)
    asum = Inventory()
    bsum = Inventory()
    account_types = get_account_types(options_map)
    for entry in filter_txns(entries):
        for posting in entry.postings:
            if posting.account in tracking_accounts:
                continue
            account_type = get_account_type(posting.account)
            if account_type in (account_types.assets, account_types.liabilities):
                asum.add_position(posting)
            elif account_type in (account_types.income, account_types.expenses):
                bsum.add_position(posting)
    csum = asum.reduce(convert.get_weight) + bsum.reduce(convert.get_weight)
    if not csum.is_small(interpolate.infer_tolerances({}, options_map)):
        errors.append(
            BudgetBalanceError(
                {'filename': '<budget_balance_check>',
                 'lineno': 0},
                f"On-budget accounts and budget total do not match: {asum} vs {-bsum}",
                None))
    return entries, errors
