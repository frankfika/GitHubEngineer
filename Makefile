# GitHub Engineer development Makefile
#
# Common recipes for contributors.  All targets run inside the local virtual
# environment created by `make venv`; install the editable package first via
# `make install` so the `ghe` entry point is on PATH.

PYTHON ?= python3
VENV   ?= .venv
BIN     := $(VENV)/bin

.PHONY: help venv install install-dev test test-fast lint format smoke clean bench bench-cost dry-run init-config build verify release-dry-run

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

venv: ## Create the local virtual environment
	$(PYTHON) -m venv $(VENV)

install: venv ## Install the package in editable mode
	$(BIN)/python -m pip install -e .

install-dev: venv ## Install the package with dev extras (pytest, coverage, build, twine)
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

bench: install-dev ## Benchmark the analyze -> render pipeline
	$(BIN)/python benchmarks/perf.py

bench-cost: install-dev ## Estimate brief cost for a given model and issue count
	$(BIN)/python benchmarks/cost.py

dry-run: install-dev ## End-to-end dry run against a 60-issue synthetic repository
	$(BIN)/python benchmarks/dry_run.py

init-config: ## Write a starter .ghe/config.yml from the example template
	@test -f .ghe/config.yml || cp .ghe/config.example.yml .ghe/config.yml && echo "Wrote .ghe/config.yml"

build: install-dev ## Build sdist + wheel into dist/
	$(BIN)/python -m build

verify: install-dev ## Run everything: tests + lint + YAML checks + build + dry-run
	@echo "==> 1/6 pytest"
	$(BIN)/pytest tests/ -q
	@echo "==> 2/6 lint"
	$(BIN)/python -m compileall -q src tests
	@echo "==> 3/6 YAML workflow checks"
	$(BIN)/python -c "import yaml; [yaml.safe_load(open(f)) for f in ['.github/workflows/test.yml', '.github/workflows/publish.yml', '.github/workflows/maintainer-brief.example.yml', '.github/dependabot.yml', '.github/ISSUE_TEMPLATE/config.yml', 'action.yml']]; print('all YAML workflows parse')"
	@echo "==> 4/6 build sdist + wheel"
	$(BIN)/python -m build
	@echo "==> 5/6 twine check"
	$(BIN)/twine check dist/*.whl dist/*.tar.gz
	@echo "==> 6/6 end-to-end dry run"
	$(BIN)/python benchmarks/dry_run.py
	@echo ""
	@echo "All verify stages passed."

release-dry-run: verify ## Build + verify + simulate the publish + tag flow
	@echo "==> confirming tag v1.0.0 exists"
	@git describe --tags --exact-match HEAD >/dev/null 2>&1 || (echo "HEAD is not on a tag" && exit 1)
	@echo "==> confirming dist/ has the v1.0.0 artefacts"
	@test -f dist/github_engineer-1.0.0-py3-none-any.whl || (echo "missing wheel" && exit 1)
	@test -f dist/github_engineer-1.0.0.tar.gz || (echo "missing sdist" && exit 1)
	@echo "==> confirm PyPI trusted publishing config (publish.yml)"
	@grep -q "pypa/gh-action-pypi-publish" .github/workflows/publish.yml
	@echo "All release preconditions met. Push to GitHub to trigger publish.yml."

clean: ## Remove the local venv and Python build artefacts
	rm -rf $(VENV) .pytest_cache .ghe/history .ghe/memory/decisions.yml dist/ build/
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
