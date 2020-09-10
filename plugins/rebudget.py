import collections
from refried import is_account_account
from beancount.core import convert
from beancount.core.data import Open, Transaction, filter_txns
from beancount.core.inventory import Inventory

__plugins__ = ('rebudget', 'balance_check')

BudgetBalanceError = collections.namedtuple('BudgetBalanceError', 'source message entry')

def rebudget_entry(entry):
    if isinstance(entry, Transaction):
        for posting in entry.postings:
            if is_account_account(posting.account):
                break
        else:
            return entry._replace(tags=(entry.tags | frozenset(('rebudget',))))
    return entry

def rebudget(entries, options_map):
    return [rebudget_entry(e) for e in entries], []

def balance_check(entries, options_map):
    errors = []
    tracking_accounts = set()
    for entry in entries:
        if isinstance(entry, Open):
            if entry.meta.get('tracking', False):
                tracking_accounts.add(entry.account)
    asum = Inventory()
    bsum = Inventory()
    for entry in filter_txns(entries):
        for posting in entry.postings:
            if posting.account in tracking_accounts:
                continue
            components = posting.account.split(':')
            if components[0] in ('Assets', 'Liabilities'):
                asum.add_position(posting)
            elif components[0] in ('Income', 'Expenses'):
                bsum.add_position(posting)
    asum = asum.reduce(convert.get_weight)
    bsum = bsum.reduce(convert.get_weight)
    if asum != -bsum:
        errors.append(
            BudgetBalanceError(
                {'filename': '<budget_balance_check>',
                 'lineno': 0},
                f"On-budget accounts and budget total do not match: {asum} vs {-bsum}",
                None))
    return entries, errors
