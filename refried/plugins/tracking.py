from beancount.core import compare
from beancount.core.data import Transaction, new_metadata

__plugins__ = ('tracking',)

def tracking(entries, options_map):
    errors = []
    new_entries = []
    for entry in entries:
        new_entry = None
        if isinstance(entry, Transaction):
            new_postings = []
            for posting in entry.postings:
                if 'tracking' in posting.meta:
                    new_meta = posting.meta.copy()
                    new_acct = new_meta.pop('tracking')
                    new_posting = posting._replace(account=new_acct, meta=new_meta)
                    new_postings.append(new_posting)
            if new_postings:
                link_id = 'tracking-' + compare.hash_entry(entry)
                new_links = entry.links | set([link_id])
                entry = entry._replace(links=new_links)
                new_entry = entry._replace(
                    postings=new_postings)
        new_entries.append(entry)
        if new_entry:
            new_entries.append(new_entry)
    return new_entries, errors
