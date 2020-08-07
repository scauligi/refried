import collections
from beancount.core.data import Open, Custom

__plugins__ = ('wishfarm',)

WishfarmError = collections.namedtuple('WishfarmError', 'source message entry')

def wishfarm(entries, options_map):
    errors = []
    wish_sprouts = {}
    for entry in entries:
        if isinstance(entry, Open):
            if 'wish_slot' in entry.meta:
                slot = entry.meta['wish_slot']
                if slot in wish_sprouts:
                    errors.append(
                        WishfarmError(
                            entry.meta,
                            f'Duplicate wish_slot: "{slot}"',
                            [wish_sprouts[slot], entry]))
                    continue
                wish_sprouts[slot] = entry
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
                sprout = wish_sprouts.pop(slot)
                sprout.meta.update({k: v for k, v in entry.meta.items() if k not in sprout.meta})
                wish_size = entry.values[0].value
                wish_name = entry.values[1].value
                sprout.meta['name'] = f'({wish_size}) {wish_name}'
    return entries, errors
