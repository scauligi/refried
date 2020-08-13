# YNAB-style budgeting

This document describes how to do YNAB-style budgeting with the help of the `avail_ext` fava extension.

## Necessary plugins

Enable the `rebudget` beancount plugin and the `avail_ext` fava extension
by adding the following lines to your beancount file:

```
plugin "refried.plugins.rebudget"
2020-01-01 custom "fava-extension" "refried.extensions.avail_ext"
```

This will add a new report "Budget" to fava. The `rebudget` plugin is
required for it to function properly.

## Usage

The "Budget" extension will display all of your Income and Expense accounts, by month.
In the style of YNAB, each account has three columns: "Budgeted", "Spent", and "Available".

Normal transactions will show up under the "Spent" columns of their respective Expense accounts.
No need to do anything special!

To (re)budget between Expense accounts, simply create a new transaction transferring money
between Income/Expense accounts. Due to the nature of double-entry bookkeeping, note that the signs
will be the opposite of what you might expect!

For example, suppose you have $3000 in unbudgeted income and you want to fill out your budget for the upcoming month:

```
2020-02-01 "Budgeting for February"
  Income:To-be-budgeted              2,000 USD
  Expenses:Obligations:Rent         -1,000 USD
  Expenses:Obligations:Utilities      -100 USD
  Expenses:Necessities:Groceries      -200 USD
  Expenses:Fun-money:Video-games      -700 USD
```

Remember, the signs appear swapped! This takes $2000 _out_ of the "To be budgeted" account and moves money _into_ the expense account categories.

Later, if you realize that you need more money for groceries (and don't need nearly as much for video games), you can rebudget money like so:

```
2020-02-13 "Need more money for fancy home dinner plans"
  Expenses:Necessities:Groceries      -300 USD
  Expenses:Fun-money:Video-games       300 USD
```

Understandably, this will wreak havoc with your (non-budgeting) expense reports. This is where the `rebudget` plugin comes in!
For any transaction that don't involve an Assets or Liabilities account, such as the ones above, the `rebudget` plugin will
automatically apply the tag `#rebudget`. So by filtering out the `#rebudget` tag you will have the correct data to use for your usual reports!
(In fava you can use the search filter `-#rebudget`.)

## YNAB-style account views

If you also want YNAB-style account views with "Working" vs "Cleared" totals and cleared vs uncleared postings, see the [YNAB-style account views](clearing.md) document.
