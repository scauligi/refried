# refried

A collection of plugins and scripts for
[beancount](https://github.com/beancount/beancount) and
[fava](https://github.com/beancount/fava) for monthly budgeting.
Budgeting-related plugins inspired by
[You Need a Budget](https://www.youneedabudget.com).

Some plugins may benefit from or require features found in
[my fork of beancount](https://github.com/scauligi/beancount).

## Installation

Make sure the following option is set in your beancount file:

```
option "insert_pythonpath" "TRUE"
```

Then clone this repository into the same directory as your beancount file:

```bash
git clone https://github.com/scauligi/refried.git
```

## Usage

### Beancount plugins

TODO

### Fava extensions

TODO

### Other notes

TODO e.g. the `Period` class

## Conventions

Many of the plugins allow you to specify more user friendly names by using a
`name: <str>` metadata on an account's `open` directive.
You can also influence the ordering of displayed accounts using an `ordering:
<number>` metadata on an account's `open` directive.

Many of the plugins may currently make assumptions about currency (USD) and
various account names.

## Attribution

refried includes content based off of files from
https://github.com/redstreet/beancount_reds_plugins, licenced under GPL3.
