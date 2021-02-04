import datetime

from beancount.core.amount import Amount
from beancount.core.data import Open, Close, Balance, new_metadata
from beancount.core.number import ZERO

__plugins__ = ('close_zero',)

def close_zero(entries, options_map):
    default_currencies = options_map['operating_currency']
    errors = []
    currencies = {}
    new_entries = []
    for entry in entries:
        if isinstance(entry, Open):
            currencies[entry.account] = entry.currencies
        elif isinstance(entry, Close):
            for currency in currencies.get(entry.account, default_currencies):
                new_entry = Balance(
                    new_metadata('<close_zero>', 0),
                    entry.date + datetime.timedelta(days=1),
                    entry.account, Amount(ZERO, currency),
                    None, None)
                new_entries.append(new_entry)
        new_entries.append(entry)
    return new_entries, errors
