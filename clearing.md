# YNAB-style account views

This document describes how to set up YNAB-style account views with "Working" vs "Cleared" amounts
with the help of the `accts_ext` and `journal_ext` fava extensions.

## Necessary plugins

Enable the `clearing` beancount plugin, as well as the `accts_ext` and `journal_ext` fava extensions
by adding the following lines to your beancount file:

```
plugin "refried.plugins.clearing"
2020-01-01 custom "fava-extension" "refried.extensions.accts_ext"
2020-01-01 custom "fava-extension" "refried.extensions.journal_ext"
```

This will add a new report "Accounts" to fava. It will also add a report "Journal" but you shouldn't use it directly.
The `clearing` plugin is required for both of these to function properly.

## Usage

The "Accounts" extension will display all of your Assets and Liabilities accounts.
In the style of YNAB, each account has a "Working" and a "Cleared" column, as well as a "Total" column.
The "Working" column shows the sum of all cleared transactions as well as all _negative_ uncleared transactions to the account.
The "Cleared" column shows the sum of all cleared transactions and the "Total" column shows the sum of all transactions.

If you click on an account, you will get sent to the account's "Journal" extension page, which will display uncleared transactions
in a different color than cleared transactions. It also has other tweaks to the standard ledger display that I prefer.

There are three ways for a posting to be marked as cleared. They are based on the attributes that [beancount-import](https://github.com/jbms/beancount-import)
uses since that's what I personally use to import transactions.

First, if an account's `open` directive has the metadata `autoclear: TRUE`, then all postings to that account will automatically be considered cleared.
This is useful for cash accounts where having uncleared postings doesn't make much sense.

Second, for ease of use, if an account's `open` directive has the metadata `cleared_before: <date>`, then all postings before that date to that account
will automatically be considered cleared. This is useful if you already have many transactions in your ledger before you start using these plugins.

Finally, if a posting has the `date:` metadata (regardless of the value), then the posting is considered cleared. If you're using
[beancount-import](https://github.com/jbms/beancount-import) then it will add the `date:` metadata to any postings it imports/matches.

If the posting has the metadata `uncleared:` attached, then it is considered not cleared regardless of any of the attributes above.
This is useful e.g. for overriding a posting to an autoclearing account.

## Under the hood

The `clearing` plugin uses the criteria above to add a metadata key `"_cleared"` to cleared postings; the "Accounts" and "Journal" extensions
check for the existence of this metadata key to determine if a posting is cleared or not. Note that according to the current beancount language
spec, `"_cleared"` is not a valid metadata key due to the leading underscore. However, in my testing, beancount and fava both still handle
this gracefully without problems. I can't make any guarantees about other plugins or tools you may be using.
