BASH_SCRIPTS := $(shell git grep --name-only '^.!/usr/bin/env bash$$')

init:
	pip install pipenv --upgrade
	pipenv install --dev --skip-lock

check-scripts:
	# Fail if any of these files have warnings
	shellcheck --source-path "$(dir $(realpath $(firstword $(MAKEFILE_LIST))))" $(BASH_SCRIPTS)

format-python:
	pipenv run yapf --in-place --parallel --recursive --verbose bash_history bash_historytests setup.py

coverage:
	pipenv run pytest --verbose --cov=bash_history --cov-report=xml --junit-xml=report.xml

lint-flake8:
	pipenv run flake8

lint-python-style:
	# Fail if yapf formatter needs to reformat code
	pipenv run yapf --diff --recursive bash_history bash_historytests setup.py

lint: lint-flake8 lint-python-style

test:
	pipenv run pytest --cov=bash_history

tests:
	pipenv run tox

ci: lint check-scripts
	pipenv run pytest -n 8 --boxed --cov=bash_history --cov-report=xml --junit-xml=report.xml

