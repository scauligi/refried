import datetime
import functools
from collections import defaultdict as ddict, OrderedDict
from beancount import loader
from beancount.core import account as acctops, data
from beancount.core.data import Open, Close, Custom, Transaction

__version__ = '0.5.2'

def halfcents(d):
    s = f'{d:,.03f}'
    if s[-1] == '0':
        s = s[:-1]
    return s

def is_account_account(account):
    return account.startswith('Assets:') or account.startswith('Liabilities:')

def load_file(*args, futures=False, **kwargs):
    entries, errors, options = loader.load_file(*args, **kwargs)
    if not futures:
        culled_entries = [entry for entry in entries
                          if (not isinstance(entry, Transaction)) or ('future' not in entry.tags)]
        entries = culled_entries
    return entries, errors, options

def filter_postings(entries):
    """A generator that yields the Postings of Transaction instances in a general list of entries.

    Args:
      entries: A list of directives.
    Yields:
      A tuple (Transaction, Posting) for each posting in each transaction.
    """
    for entry in entries:
        if isinstance(entry, Transaction):
            for posting in entry.postings:
                yield entry, posting

# derived from beancount.core.getters.get_account_open_close()
def get_account_entries(entries):
    """Fetch the open/close entries for each of the accounts,
    as well as custom entries for non-account groups.

    If an entry happens to be duplicated, accept the earliest
    entry (chronologically).

    Args:
      entries: A list of directive instances.
    Returns:
      A map of account name strings to pairs of (open/custom-directive, close-directive)
      tuples.
    """
    # A dict of account name to (open/custom-entry, close-entry).
    open_close_map = ddict(lambda: [None, None])
    for entry in entries:
        if not isinstance(entry, (Open, Close, Custom)):
            continue
        if isinstance(entry, Custom):
            if not entry.type == "group-meta":
                continue
            acct = entry.values[0].value
        else:
            acct = entry.account
        open_close = open_close_map[acct]
        index = 0 if isinstance(entry, (Open, Custom)) else 1
        previous_entry = open_close[index]
        if previous_entry is not None:
            if previous_entry.date <= entry.date:
                entry = previous_entry
        open_close[index] = entry

    return dict(open_close_map)

def aname(open_close, a, prefix=''):
    """Retrieve a name for an account/group.
    If the account/group has an associated `name:` metadata
    then return that, else return the final component of the account string.

    Args:
      open_close: The dictionary returned from `refried.get_account_entries()`.
      a: The account/group string.
      prefix: A string to use for tree-like nesting/indentation.
    Returns:
      The associated name for the account.
    """
    components = acctops.split(a)
    start = prefix * (len(components) - 1)
    if a not in open_close:
        rest = components[-1]
    else:
        rest = open_close[a][0].meta.get('name', components[-1])
    return start + rest

def isopen(open_close_entry, start, end=None):
    """A predicate for whether an account is open during a given time frame.

    Args:
      open_close_entry: The value associated with an account's key in the dictionary
        returned from `refried.get_account_entries()`.
      start: A `datetime.date` or `Period` for the start of the time frame (inclusive).
      end: An optional `datetime.date` or `Period` for the end of the time frame (exclusive).
    Returns:
      `True` if the account is open and not closed during any date within the time frame.
    """
    open, close = open_close_entry
    assert open is not None
    if isinstance(start, Period):
        start = start.asdate()
    if end is None:
        end = start + datetime.timedelta(days=1)
    elif isinstance(end, Period):
        end = end.asdate()
    if open.date >= end:
        return False
    if close is None:
        return True
    if close.date <= start:
        return False
    return True

def _reverse_parents(a):
    chain = acctops.split(a)
    for i in range(len(chain)):
        yield acctops.join(*chain[:i+1])

def _generate_account_order(open_close):
    ordermap = ddict(lambda: (999999,))
    for a, (o, _) in open_close.items():
        if 'ordering' in o.meta:
            order = str(o.meta['ordering']).split('.')
            ordermap[a] = tuple(int(x) for x in order)
    def account_order(cat):
        a, _ = cat
        return tuple(ordermap[chain] for chain in _reverse_parents(a))
    return account_order

def _accounts_sorted(open_close, start=None, end=None):
    account_order = _generate_account_order(open_close)
    cats = open_close.items()
    if start is not None:
        cats = filter(lambda cat: isopen(cat[1], start, end), cats)
    return sorted(cats, key=account_order)

def walk(open_close, root, start=None, end=None):
    """A generator that yields accounts/groups in preorder... order.
    Respects `ordering:` metadata, otherwise asciibetic by account name.

    Args:
      open_close: The dictionary returned from `refried.get_account_entries()`.
      root: The account string of the root node to start from.
      start: (optional) Limits accounts to those that are `refried.isopen()` during this time frame.
      end: (optional) Limits accounts to those that are `refried.isopen()` during this time frame.
    Yields:
      Tuples (account string, Open/Custom directive) in preorder traversal.
    """
    accts = _accounts_sorted(open_close, start, end)
    accts = filter(lambda cat: cat[0].startswith(root), accts)
    seen = set()
    for a, (o, _) in accts:
        for parent in _reverse_parents(acctops.parent(a)):
            if parent not in seen:
                seen.add(parent)
                yield parent, None
        seen.add(a)
        yield a, o

def tree(open_close, start=None, end=None):
    """Creates a tree (using `dict`s) of account/groups.
    Respects `ordering:` metadata, otherwise asciibetic by account name.

    Args:
      open_close: The dictionary returned from `refried.get_account_entries()`.
      start: (optional) Limits accounts to those that are `refried.isopen()` during this time frame.
      end: (optional) Limits accounts to those that are `refried.isopen()` during this time frame.
    Returns:
      A recursive `dict` of account string -> (Open/Custom directive, subtree of children).
    """
    accts = _accounts_sorted(open_close, start, end)
    seen = set()
    tree = dict()
    for a, (o, _) in accts:
        subtree = tree
        for parent in _reverse_parents(acctops.parent(a)):
            subtree = subtree.setdefault(parent, (None, OrderedDict()))[1]
            if parent not in seen:
                seen.add(parent)
        subtree[a] = (o, OrderedDict())
    return tree

@functools.total_ordering
class Period:
    """Useful class for working with month-based timeframes."""
    def __init__(self, year, month):
        self.year = year
        self.month = month
        self._date = datetime.date(year, month, 1)

    @staticmethod
    def from_str(s):
        """Expects string in the form "{year}-{month}"."""
        year, month = (int(n) for n in s.split('-'))
        return Period(year, month)

    @staticmethod
    def from_date(date):
        """Takes year and month from a `datetime.date`."""
        return Period(date.year, date.month)

    @staticmethod
    def from_canonical(canon):
        """Converts from a canonical `int` representation."""
        year, month0 = divmod(canon, 12)
        return Period(year, month0 + 1)

    def __hash__(self):
        return hash((self.year, self.month))

    def __str__(self):
        return f'{self.year:04}-{self.month:02}'

    def __repr__(self):
        return f'Period({self.year}, {self.month})'

    def __eq__(self, o):
        if not isinstance(o, Period):
            return NotImplemented
        return (self.year, self.month) == (o.year, o.month)

    def __gt__(self, o):
        if not isinstance(o, Period):
            return NotImplemented
        return (self.year, self.month) > (o.year, o.month)

    def canonical(self):
        """Converts to a canonical `int` representation."""
        return self.year * 12 + self.month - 1

    def asdate(self):
        """Creates a `datetime.date` for the first date in this period."""
        return self._date

    def add(self, months):
        """Returns a new `Period` advanced by a number of months."""
        return Period.from_canonical(self.canonical() + months)

    def sub(self, months):
        """Returns a new `Period` regressed by a number of months."""
        return self.add(-months)
