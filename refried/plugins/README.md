# Plugins

(this document is still a WIP)

## clearing

Applies metadata to postings for assets/liabilities signifying whether they
have cleared in their corresponding accounts or not.
See [the document on YNAB-style account views](/docs/clearing.md) for details.

## effective_date

Creates linked transactions based on `effective_date:` metadata on postings.

Can be specified multiple times to split the amount among the different dates, a la the `split` plugin.

Useful for sending income to be budgeted in a future period.
Also useful for incrementally budgeting money into a category throughout the month (e.g., adding $20 every week
to a "Dining Out" category).

See [the document on automatically budgeting towards goals](/docs/goals.md) for details.

Based off of
https://github.com/redstreet/beancount_reds_plugins, licensed under GPL3.

## evensplit

Creates additional postings in a transaction according to `split:` metadata on postings.

Can be specified multiple times to split the amount among several accounts.

Can specify a string to create special "reimbursement" postings.

## rebudget

Applies the `#rebudget` tag to (re)budgeting transactions so they can be
easily filtered away for reports.
See [the document on YNAB-style budgeting](/docs/budgeting.md) for details.

Also checks that the amount of money in on-budget (non-tracking) accounts matches the
amount of money in on-budget (non-tracking) income/expense categories.
See [the document on tracking accounts](/docs/tracking.md) for details.

## tracking

Creates linked transactions based on `tracking:` metadata on postings.
See [the document on tracking accounts](/docs/tracking.md) for details.

## wishfarm

Helper plugin for managing a [wish farm](https://www.youneedabudget.com/wish-lists/).
