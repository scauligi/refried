from beancount.core.data import Transaction, Posting, Amount, Cost, filter_txns
from beancount.core.account import is_valid as is_account
from beancount.core.amount import div as adiv
from beancount.core.number import D

__plugins__ = ('evensplit',)

def evensplit(entries, options_map):
    errors = []
    for entry in filter_txns(entries):
        i = 0
        while i < len(entry.postings):
            posting = entry.postings[i]
            if posting.meta and 'split' in posting.meta:
                targets = posting.meta.pop('split')
                if is_account(targets):
                    # special case for single split to account (because halfcents)
                    amount = adiv(posting.units, D(2))
                    entry.postings[i] = posting._replace(units=amount)
                    newacct = targets
                    ometa = posting.meta.copy()
                    i += 1
                    entry.postings.insert(i, Posting(newacct, amount, None, None, None, ometa))
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
                        entry.postings[i] = posting._replace(units=remainder)
                    else:
                        entry.postings.pop(i)
                        i -= 1
                    for target in targets:
                        if is_account(target):
                            newacct = target
                            newamount = amount
                            newcost = None
                        else:
                            newacct = "Assets:Receivables"
                            newamount = Amount(D(1), "REIMB")
                            newcost = Cost(amount.number, amount.currency, entry.date, target)
                        ometa = posting.meta.copy()
                        i += 1
                        entry.postings.insert(i, Posting(newacct, newamount, newcost, None, None, ometa))
            i += 1
    return entries, errors
