# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['refried',
 'refried.extensions.accts_ext',
 'refried.extensions.avail_ext',
 'refried.extensions.journal_ext',
 'refried.plugins']

package_data = \
{'': ['*'],
 'refried.extensions.accts_ext': ['templates/*'],
 'refried.extensions.avail_ext': ['templates/*'],
 'refried.extensions.journal_ext': ['templates/*']}

setup_kwargs = {
    'name': 'beancount-refried',
    'version': '0.5.2',
    'description': 'A collection of plugins and scripts for beancount and fava for monthly budgeting.',
    'long_description': '# refried\n\nA collection of plugins and scripts for\n[beancount](https://github.com/beancount/beancount) and\n[fava](https://github.com/beancount/fava) for monthly budgeting.\nBudgeting-related plugins inspired by\n[You Need a Budget](https://www.youneedabudget.com).\n\n## Installation\n\nInstall this plugin from PyPI:\n\n```bash\npip install beancount-refried\n```\n\nAlternatively, if you want to be able to edit the plugins locally,\nyou can clone this repository then run the following from within\nthe root of the repository:\n\n```bash\npip install -e .\n```\n\n## Quick start\n\nEnable the `rebudget` beancount plugin and the `avail_ext` fava extension\nby adding the following lines to your beancount file:\n\n```\nplugin "refried.plugins.rebudget"\n2020-01-01 custom "fava-extension" "refried.extensions.avail_ext"\n```\n\nThis will add a new report "Budget" to fava. The `rebudget` plugin is\nrequired for it to function properly.\n\nSee the document on [YNAB-style budgeting](docs/budgeting.md) for details.\n\n## Customization\n\nThe fava extensions allow you to specify more user friendly names by using a\n`name: <str>` metadata on an account\'s `open` directive.\n\nYou can also influence the ordering of displayed accounts using an `ordering:\n<number>` metadata on an account\'s `open` directive if you don\'t want the\ndefault alphabetic ordering.\nYou can also use Decimals or strings of the form "<number>.<number>.<number>..."\nto easily insert new accounts between two adjacent accounts.\nFor example, "23.64.2" would be ordered between "23.64" and "23.65".\n\nSome of the plugins/extensions may currently make assumptions about currency (USD) and\nvarious account names.\n\n## Attribution\n\nrefried includes content based off of files from\nhttps://github.com/redstreet/beancount_reds_plugins, licensed under GPL3.\n',
    'author': 'scauligi',
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/scauligi/refried',
    'packages': packages,
    'package_data': package_data,
    'python_requires': '>=3.6,<4.0',
}


setup(**setup_kwargs)
