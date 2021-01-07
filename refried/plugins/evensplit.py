from collections import defaultdict as ddict
from copy import deepcopy
from beancount.core.data import Transaction, Posting, Amount, Cost, filter_txns
from beancount.core.account import is_valid as is_account
from beancount.core.amount import div as adiv
from beancount.core.number import D

__plugins__ = ('evensplit',)

def add_posting(posting_map, acct, amt, save_meta):
    old_amt, meta = posting_map[(acct, amt.currency)]
    new_amt = old_amt + amt.number
    if save_meta:
        for key, value in save_meta.items():
            if key in meta:
                # XXX if no multimeta, do something else
                if not isinstance(meta[key], list):
                    meta[key] = [meta[key]]
                if isinstance(value, list):
                    meta[key].extend(value)
                else:
                    meta[key].append(value)
            else:
                meta[key] = value
    posting_map[(acct, amt.currency)] = (new_amt, meta)

def evensplit(entries, options_map):
    errors = []
    for entry in filter_txns(entries):
        new_postings_map = ddict(lambda: (D(), {}))
        special_postings = []

        for i, posting in enumerate(entry.postings):
            if posting.meta and 'split' in posting.meta:
                assert posting.cost is None

                save_meta = deepcopy(posting.meta)
                targets = save_meta.pop('split')

                if is_account(targets):
                    # special case for single split to account (because halfcents)
                    assert posting.account != "Assets:Receivables"
                    amount = adiv(posting.units, D(2))
                    posting = posting._replace(units=amount)
                    newacct = targets
                    add_posting(new_postings_map, newacct, amount, save_meta)
                else:
                    if not isinstance(targets, list):
                        targets = [targets]
                    ntargets = len(targets)
                    if posting.account != "Assets:Receivables":
                        ntargets += 1
                    split_amount = posting.units.number / ntargets
                    split_amount = round(split_amount, 2)
                    amount = posting.units._replace(number=split_amount)

                    if posting.account != "Assets:Receivables":
                        remainder = posting.units.number - split_amount * len(targets)
                        remainder = posting.units._replace(number=remainder)
                        posting = posting._replace(units=remainder)
                    else:
                        posting = None

                    for target in targets:
                        if is_account(target):
                            newacct = target
                            newamount = amount
                            newcost = None
                            add_posting(new_postings_map, newacct, newamount, save_meta)
                        else:
                            newacct = "Assets:Receivables"
                            newamount = Amount(D(1), "REIMB")
                            newcost = Cost(amount.number, amount.currency, entry.date, target)
                            special_postings.append(Posting(newacct, newamount, newcost, None, None, save_meta))

                entry.postings[i] = posting

        entry.postings[:] = list(filter(lambda x: x is not None, entry.postings))
        for (acct, currency), (amt, meta) in new_postings_map.items():
            entry.postings.append(Posting(acct, Amount(amt, currency), None, None, None, meta))
        entry.postings.extend(special_postings)
    return entries, errors
