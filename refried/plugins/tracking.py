from beancount.core import compare
from beancount.core.data import Open, Posting, Transaction
from beancount.core.account_types import is_account_type
from beancount.core.inventory import Inventory
from beancount.parser.options import get_account_types

__plugins__ = ('tracking',)

def tracking(entries, options_map):
    account_types = get_account_types(options_map)
    income_tracking = set()
    expense_tracking = set()

    errors = []
    new_entries = []
    for entry in entries:
        new_entry = None
        if isinstance(entry, Open) and entry.meta.get('tracking', False):
            if is_account_type(account_types.expenses, entry.account):
                expense_tracking.add(entry.account)
            elif is_account_type(account_types.income, entry.account):
                income_tracking.add(entry.account)
        elif isinstance(entry, Transaction):
            new_postings = []
            tracking_balance = Inventory()
            for posting in entry.postings:
                if 'tracking' in posting.meta:
                    new_acct = posting.meta['tracking']
                    new_posting = posting._replace(account=new_acct, meta=None)
                    new_postings.append(new_posting)
                    tracking_balance.add_position(posting)
            if new_postings:
                for position in -tracking_balance:
                    if position.units.number < 0 and len(income_tracking) == 1:
                        posting_acct ,= income_tracking
                    elif position.units.number > 0 and len(expense_tracking) == 1:
                        posting_acct ,= expense_tracking
                    else:
                        continue
                    new_posting = Posting(posting_acct, position.units, position.cost, None, None, None)
                    new_postings.append(new_posting)

                link_id = 'tracking-' + compare.hash_entry(entry)
                new_links = entry.links | set([link_id])
                entry = entry._replace(links=new_links)
                new_entry = entry._replace(
                    postings=new_postings)
        new_entries.append(entry)
        if new_entry:
            new_entries.append(new_entry)
    return new_entries, errors
