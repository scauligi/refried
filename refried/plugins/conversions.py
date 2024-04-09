import typing

from beancount.core.data import Amount, Posting, Transaction
from beancount.core.inventory import Inventory
from more_itertools import flatten, unzip

__plugins__ = ('conversions',)


class TestError(typing.NamedTuple):
    source: dict
    message: str
    entry: None = None


# TestError = collections.namedtuple('TestError', 'source message entry')


def conversions(entries, options_map):
    def do_conversion(entry):
        if not isinstance(entry, Transaction):
            return entry, []
        errors = []
        if 'convert_at' in entry.meta or any(
            'convert_at' in posting.meta for posting in entry.postings
        ):
            conversion_account = None
            conversion_meta = {}
            postings = []
            inv = Inventory()
            for posting in entry.postings:
                if posting.meta.get('__automatic__'):
                    conversion_account = posting.account
                    conversion_meta = posting.meta
                elif price := (
                    posting.meta.get('convert_at') or entry.meta.get('convert_at')
                ):
                    inv.add_position(posting)
                    num = -posting.units.number * price.number
                    num = options_map['dcontext'].quantize(num, price.currency)
                    units = Amount(num, price.currency)
                    new_posting = Posting(posting.account, units, None, None, None, posting.meta)
                    inv.add_position(new_posting)
                    postings.extend((posting, new_posting))
                else:
                    postings.append(posting)
            if conversion_account:
                for position in inv:
                    postings.append(
                        Posting(
                            conversion_account, -position.units, None, None, None, conversion_meta
                        )
                    )
            entry = entry._replace(postings=postings)
        return entry, errors

    entries, errors = unzip(map(do_conversion, entries))
    return list(entries), list(flatten(errors))
