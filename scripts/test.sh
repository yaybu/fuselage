#! /bin/sh
set -e
alias python="poetry run python"
poetry run find . -name '*.py' -exec pyupgrade --py37-plus {} +
python -m black tests fuselage
python -m isort tests fuselage
python -m black tests fuselage --check --diff
python -m flake8 tests fuselage
python -m pytest tests
