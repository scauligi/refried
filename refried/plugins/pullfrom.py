from beancount.core import compare
from beancount.core.data import Posting, Transaction, new_metadata
from beancount.core.inventory import Inventory
from beancount.parser.options import get_account_types

__plugins__ = ('pullfrom',)

def pullfrom(entries, options_map):
    errors = []
    new_entries = []
    for entry in entries:
        add_entries = []
        if isinstance(entry, Transaction):
            new_postings = []
            for posting in entry.postings:
                if 'pull_from' in posting.meta:
                    memo = posting.meta.get('memo', '')
                    new_acct = posting.meta['pull_from']
                    new_posting = posting._replace(units=-posting.units, meta=None)
                    new_postings.append(new_posting)
                    new_posting = posting._replace(account=new_acct, meta=None)
                    new_postings.append(new_posting)

                    link_id = set(['pull-' + compare.hash_entry(entry)])
                    new_links = entry.links | link_id
                    entry = entry._replace(links=new_links)
                    new_meta = posting.meta.copy()
                    del new_meta['pull_from']
                    new_meta.pop('memo', None)
                    new_meta['filename'] = entry.meta['filename']
                    new_meta['lineno'] = entry.meta['lineno']
                    new_entry = entry._replace(
                        payee=None,
                        narration=memo,
                        tags=set(),
                        links=link_id,
                        meta=new_meta,
                        postings=new_postings)
                    add_entries.append(new_entry)
        new_entries.append(entry)
        new_entries.extend(add_entries)
    return new_entries, errors
