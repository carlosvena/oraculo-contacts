#!/usr/bin/env sh
set -eu
python -m ruff check .
python -m ruff format --check .
python -m pytest --cov

