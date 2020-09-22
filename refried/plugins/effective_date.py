"""Beancount plugin to implement per-posting effective dates.
Modified from https://github.com/redstreet/beancount_reds_plugins, under GPL3"""

import collections
from beancount.core.amount import ZERO
from beancount.core import data
from beancount.core import account
from beancount.core import getters
from beancount.core import flags
from beancount.ops import holdings
from beancount.parser import options
from beancount.parser import printer
from ast import literal_eval
from decimal import Decimal
import copy
import datetime
import time
import string

DEBUG = False

__plugins__ = ('effective_date',)

LINK_FORMAT = 'edate-{date}-{index}'

def has_valid_effective_date(posting):
    return posting.meta is not None and \
             'effective_date' in posting.meta and \
             (isinstance(posting.meta['effective_date'], datetime.date) \
              or (isinstance(posting.meta['effective_date'], list) \
                  and all(isinstance(el, datetime.date) for el in posting.meta['effective_date'])))

def has_posting_with_valid_effective_date(entry):
    for posting in entry.postings:
        if has_valid_effective_date(posting):
            return True
    return False

def create_new_effective_date_entry(entry, date, hold_posting, original_posting):
    def cleaned(p):
       clean_meta = copy.deepcopy(p.meta)
       clean_meta.pop('effective_date', None)
       return p._replace(meta=clean_meta)

    new_meta = {'original_date': entry.date}
    new_meta = {**entry.meta, **new_meta}
    new_meta['filename'] = '<effective_date>'
    new_meta['lineno'] = 0
    effective_date_entry = entry._replace(date=date,
            meta={**entry.meta, **new_meta},
            postings=[cleaned(hold_posting), cleaned(original_posting)])
    return effective_date_entry

def build_config(config):
    holding_accts = {}
    if config:
        holding_accts = literal_eval(config)
    if not holding_accts:
        if DEBUG:
            print("Using default config")
        holding_accts = {
            'Expenses': 'Equity:Hold:Expenses',
            'Income':   'Income:To-Be-Budgeted:Future-Budgeted',
            'Assets':   'Equity:Hold:Assets',
        }
    return holding_accts

def effective_date(entries, options_map, config=None):
    """Effective dates

    Args:
      entries: a list of entry instances
      options_map: a dict of options parsed from the file
      config: A configuration string, which is intended to be a Python dict
        mapping match-accounts to a pair of (negative-account, position-account)
        account names.
    Returns:
      A tuple of entries and errors.

    """
    start_time = time.time()
    errors = []
    holding_accts = build_config(config)

    interesting_entries = []
    filtered_entries = []
    new_accounts = set()
    for entry in entries:
        if isinstance(entry, data.Transaction) and has_posting_with_valid_effective_date(entry):
            interesting_entries.append(entry)
        else:
            filtered_entries.append(entry)

    # add a link to each effective date entry. this gets copied over to the newly created effective date
    # entries, and thus links each set of effective date entries
    interesting_entries_linked = []
    for n, entry in enumerate(interesting_entries):
        index_string = f'{n:04}'
        date = str(entry.date).replace('-', '')
        link = LINK_FORMAT.format(date=str(date), index=index_string)
        new_entry = entry._replace(links=(entry.links or set()) | set([link]))
        interesting_entries_linked.append(new_entry)

    new_entries = []
    for entry in interesting_entries_linked:
        modified_entry_postings = []
        effective_date_entry_postings = []
        for posting in entry.postings:
            if not has_valid_effective_date(posting):
                modified_entry_postings += [posting]
            else:
                found_acct = ''
                for acct in holding_accts:
                    if posting.account.startswith(acct):
                        found_acct = acct

                new_dates = posting.meta['effective_date']
                if not isinstance(new_dates, list):
                    new_dates = [new_dates]

                unum = posting.units.number
                exp = unum.as_tuple().exponent  # produces -number_of_decimal_places
                n_ways = len(new_dates)
                overflow = unum.remainder_near(Decimal(n_ways).scaleb(exp))
                units_list = [round(unum / n_ways, abs(exp))] * n_ways
                for i in range(abs(int(overflow.scaleb(-exp)))):
                    if overflow < 0:
                        i = -1 - i
                    units_list[i] += Decimal(1).scaleb(exp)
                for i in range(len(units_list)):
                    units_list[i] = posting.units._replace(number=units_list[i])

                for new_date, units in zip(new_dates, units_list):
                    new_acct_name = holding_accts[found_acct]

                    # Replace posting in original entry with holding account
                    clean_meta = copy.deepcopy(posting.meta)
                    clean_meta['effective_date'] = new_date
                    new_posting = posting._replace(account=new_acct_name, units=units, meta=clean_meta)
                    new_accounts.add(new_posting.account)
                    modified_entry_postings.append(new_posting)

                    # Create new entry at effective_date
                    hold_posting = new_posting._replace(units=-units)
                    partial_posting = posting._replace(units=units)
                    new_entry = create_new_effective_date_entry(entry, new_date, hold_posting, partial_posting)
                    new_entries.append(new_entry)
        modified_entry = entry._replace(postings=modified_entry_postings)
        new_entries.append(modified_entry)

    # if DEBUG:
    #     print("Output results:")
    #     for e in new_entries:
    #         printer.print_entry(e)

    if DEBUG:
        elapsed_time = time.time() - start_time
        print("effective_date [{:.1f}s]: {} entries inserted.".format(elapsed_time, len(new_entries)))

    new_open_entries = create_open_directives(new_accounts, entries)
    retval = new_open_entries + new_entries + filtered_entries
    return(retval, errors)

def create_open_directives(new_accounts, entries):
    if not entries:
        return []
    # Ensure that the accounts we're going to use to book the postings exist, by
    # creating open entries for those that we generated that weren't already
    # existing accounts.
    earliest_date = entries[0].date
    open_entries = getters.get_account_open_close(entries)
    new_open_entries = []
    for account_ in sorted(new_accounts):
        if account_ not in open_entries:
            meta = data.new_metadata('<effective_date>', 0)
            open_entry = data.Open(meta, earliest_date, account_, None, None)
            new_open_entries.append(open_entry)
    return new_open_entries
