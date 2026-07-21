# GitHub Engineer development Makefile
#
# Common recipes for contributors.  All targets run inside the local virtual
# environment created by `make venv`; install the editable package first via
# `make install` so the `ghe` entry point is on PATH.

PYTHON ?= python3
VENV   ?= .venv
BIN     := $(VENV)/bin

.PHONY: help venv install install-dev test test-fast lint format smoke clean

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

venv: ## Create the local virtual environment
	$(PYTHON) -m venv $(VENV)

install: venv ## Install the package in editable mode
	$(BIN)/python -m pip install -e .

install-dev: venv ## Install the package with dev extras (pytest, coverage)
	$(BIN)/python -m pip install -e ".[dev]"

test: install-dev ## Run the full test suite
	$(BIN)/pytest tests/ -v

test-fast: install-dev ## Run the test suite without verbose output
	$(BIN)/pytest tests/ -q

lint: ## Run a minimal Python syntax check on the package
	$(BIN)/python -m compileall -q src tests

format: ## Auto-format the package and tests with the standard library
	$(BIN)/python -m py_compile src/*.py tests/*.py

smoke: install-dev ## Quick e2e: list decisions and read the example config
	$(BIN)/python -m src.main --list-decisions
	$(BIN)/python -c "import yaml; yaml.safe_load(open('.ghe/config.example.yml')); print('config.example.yml parses')"

clean: ## Remove the local venv and Python build artefacts
	rm -rf $(VENV) .pytest_cache .ghe/history .ghe/memory/decisions.yml
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
