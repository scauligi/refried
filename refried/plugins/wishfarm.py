import collections
from beancount.core.data import Open, Custom
from beancount.core import account as acctops

__plugins__ = ('wishfarm',)

WishfarmError = collections.namedtuple('WishfarmError', 'source message entry')

def wishfarm(entries, options_map):
    errors = []
    wish_sprouts = {}
    for entry in entries:
        if isinstance(entry, Open):
            if 'wish_slot' in entry.meta:
                slot = entry.meta['wish_slot']
                if 'name' in entry.meta:
                    errors.append(
                        WishfarmError(
                            entry.meta,
                            'name should be handled by wishfarm plugin',
                            [entry]))
                    continue
                tag = entry.meta.get('tag')
                if tag is None:
                    tag = acctops.split(entry.account)[-1]
                if slot in wish_sprouts:
                    errors.append(
                        WishfarmError(
                            entry.meta,
                            f'Duplicate wish_slot: "{slot}"',
                            [wish_sprouts[slot], entry]))
                    continue
                wish_sprouts[slot] = (entry, tag)
                entry.meta['name'] = f'({tag}) ...'
    for entry in entries:
        if isinstance(entry, Custom) and entry.type == "wish-list":
            if 'wish_slot' in entry.meta:
                slot = entry.meta['wish_slot']
                if slot not in wish_sprouts:
                    errors.append(
                        WishfarmError(
                            entry.meta,
                            f'Unavailable wish_slot: "{slot}"',
                            entry))
                    continue
                sprout, slot_name = wish_sprouts.pop(slot)
                wish_name = entry.values[0].value
                sprout.meta['wish_name'] = wish_name
                sprout.meta['wish_filename'] = entry.meta['filename']
                sprout.meta['wish_lineno'] = entry.meta['lineno']
                sprout.meta.update({k: v for k, v in entry.meta.items() if k not in sprout.meta})
                sprout.meta['name'] = f'({slot_name}) {wish_name}'
    return entries, errors
