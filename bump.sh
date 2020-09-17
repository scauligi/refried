#!/bin/bash
set -eu

pytest

poetry version "$@"
version=$(grep '^version' pyproject.toml | sed -E 's/^version = "(.*)"/\1/')
sed -i "s/__version__ =.*/__version__ = '$version'/" refried/__init__.py
sed -i "s/__version__ =.*/__version__ == '$version'/" tests/test_refried.py

rm -rf dist
poetry build -f sdist
tar xf dist/beancount-refried-*.tar.gz --strip-components=1
