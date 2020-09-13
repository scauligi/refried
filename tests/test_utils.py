import io
import hashlib
import contextlib

from beancount.parser import cmptest, printer
from beancount.core import compare

class TestCase(cmptest.TestCase):
    def assertEqualEntries(self, expected_entries, actual_entries):
        return assertEqualEntriesIncludingMeta(expected_entries, actual_entries, self.fail)
    def assertIncludesEntries(self, subset_entries, entries):
        raise NotImplementedError
    def assertExcludesEntries(self, subset_entries, entries):
        raise NotImplementedError

@contextlib.contextmanager
def meta_hashed_entries():
    old_ignored_names = compare.IGNORED_FIELD_NAMES.copy()
    old_stable_hash_namedtuple = compare.stable_hash_namedtuple
    compare.IGNORED_FIELD_NAMES.remove('meta')
    compare.stable_hash_namedtuple = stable_hash_namedtuple
    try:
        yield
    finally:
        compare.IGNORED_FIELD_NAMES = old_ignored_names
        compare.stable_hash_namedtuple = old_stable_hash_namedtuple

def assertEqualEntriesIncludingMeta(*args, **kwargs):
    with meta_hashed_entries():
        return cmptest.assertEqualEntries(*args, **kwargs)

IGNORE_META = ('filename', 'lineno', '__tolerances__', '__automatic__')

# Taken from beancount.core.compare.stable_hash_namedtuple
def stable_hash_namedtuple(objtuple, ignore=frozenset()):
    hashobj = hashlib.md5()
    for attr_name, attr_value in zip(objtuple._fields, objtuple):
        if attr_name in ignore:
            continue
        if isinstance(attr_value, (list, set, frozenset)):
            subhashes = set()
            for element in attr_value:
                if isinstance(element, tuple):
                    subhashes.add(stable_hash_namedtuple(element, ignore))
                else:
                    md5 = hashlib.md5()
                    md5.update(str(element).encode())
                    subhashes.add(md5.hexdigest())
            for subhash in sorted(subhashes):
                hashobj.update(subhash.encode())
        elif isinstance(attr_value, dict):
            subhashes = set()
            for key, value in attr_value.items():
                if key in IGNORE_META:
                    continue
                md5 = hashlib.md5()
                md5.update(str((key, value)).encode())
                subhashes.add(md5.hexdigest())
            for subhash in sorted(subhashes):
                hashobj.update(subhash.encode())
        else:
            hashobj.update(str(attr_value).encode())
    return hashobj.hexdigest()
