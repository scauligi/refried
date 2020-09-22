from refried import is_account_account
from beancount.core.data import Open, Transaction

__plugins__ = ['clearing']

def clearing(entries, options_map):
    errors = []
    cleardates = {}
    autoclears = {}
    for entry in entries:
        if isinstance(entry, Open):
            cleardates[entry.account] = entry.meta.get('cleared_before', None)
            autoclears[entry.account] = entry.meta.get('autoclear', False)
        elif isinstance(entry, Transaction):
            for i, posting in enumerate(entry.postings):
                if not posting.meta:
                    posting = posting._replace(meta={})
                    entry.postings[i] = posting
                if not is_account_account(posting.account):
                    if 'uncleared' in posting.meta:
                        del posting.meta['uncleared']
                    continue
                cleared = False
                if 'date' in posting.meta:
                    cleared = True
                if 'uncleared' in posting.meta:
                    del posting.meta['uncleared']
                    cleared = False
                elif posting.account not in cleardates:
                    # account doesn't have a corresponding Open directive!
                    continue
                elif (autoclears[posting.account]) or \
                        (cleardates[posting.account] and \
                         entry.date < cleardates[posting.account]):
                    cleared = True
                posting.meta['_cleared'] = cleared
    return entries, errors
