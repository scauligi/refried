from beancount.core import compare
from beancount.core.account import parent
from beancount.core.data import Open, Posting, Transaction, new_metadata
from beancount.core.inventory import Inventory
from beancount.parser.options import get_account_types

__plugins__ = ('pullfrom',)

AUTOKEYS = ['autopull', 'autodraw']
KEYS = ['pull_from', 'pull-from', 'draw_from', 'draw-from']

def pullfrom(entries, options_map):
    errors = []
    autopulls = {}
    new_entries = []
    def get_newacct(posting):
        for key, val in reversed(posting.meta.items()):
            if key in KEYS:
                return val
        key = posting.account
        while key in autopulls:
            key = autopulls[key]
            assert key != posting.account
        return key
    for entry in entries:
        add_entries = []
        if isinstance(entry, Open):
            if any(entry.meta.get(key) for key in AUTOKEYS):
                autopulls[entry.account] = parent(entry.account)
        elif isinstance(entry, Transaction):
            for posting in entry.postings:
                if posting.meta is None:
                    continue
                if any(key in posting.meta for key in KEYS) or posting.account in autopulls:
                    new_postings = []
                    memo = posting.meta.get('memo', '')
                    new_acct = get_newacct(posting)
                    new_posting = posting._replace(units=-posting.units, meta=None)
                    new_postings.append(new_posting)
                    new_posting = posting._replace(account=new_acct, meta=None)
                    new_postings.append(new_posting)

                    link_id = set(['pull-' + compare.hash_entry(entry)])
                    new_links = entry.links | link_id
                    entry = entry._replace(links=new_links)
                    new_meta = posting.meta.copy()
                    for key in [*KEYS, 'memo']:
                        new_meta.pop(key, None)
                    new_meta['filename'] = entry.meta['filename']
                    new_meta['lineno'] = entry.meta['lineno']
                    new_entry = entry._replace(
                        payee=None,
                        narration=memo,
                        # tags=set(),
                        links=link_id,
                        meta=new_meta,
                        postings=new_postings)
                    add_entries.append(new_entry)
        new_entries.append(entry)
        new_entries.extend(add_entries)
    return new_entries, errors
