# Set python virtual environment
export PIPENV_VENV_IN_PROJECT=1
VENV := ./.venv

SHELL = /usr/bin/env bash -eo pipefail

deps: ${VENV}

${VENV}:
	pip install pipenv
	pipenv install --dev

lint: ${VENV}
	 pipenv run pylint --rcfile=.pylintrc *.py connectors

test: ${VENV}
	ENV=test PYTHONDONTWRITEBYTECODE=1 pipenv run coverage run -m pytest -W ignore::DeprecationWarning
	pipenv run coverage report -m
