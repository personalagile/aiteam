SHELL := /bin/sh

# Virtualenv and tool paths
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
RUFF := $(VENV)/bin/ruff
BLACK := $(VENV)/bin/black
ISORT := $(VENV)/bin/isort
PYLINT := $(VENV)/bin/pylint
PYTEST := $(VENV)/bin/pytest
MYPY := $(VENV)/bin/mypy
PRECOMMIT := $(VENV)/bin/pre-commit
DAPHNE := $(VENV)/bin/daphne
CELERY := $(VENV)/bin/celery
SPHINXBUILD := $(VENV)/bin/sphinx-build
MANAGE := $(PY) manage.py

# Project packages
PACKAGES := aiteam apps agents_core memory orchestrator tools

.DEFAULT_GOAL := help

.PHONY: help init install pre-commit fmt format lint type test cov check ci run daphne celery docs clean env

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "  \\033[36m%-16s\\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

init: ## Create virtualenv in .venv (if missing) and upgrade pip/setuptools/wheel
	@test -d $(VENV) || python3 -m venv $(VENV)
	$(PIP) install -U pip setuptools wheel

install: init ## Install project with all extras (agents, web, docs, dev)
	$(PIP) install -e '.[agents,web,docs,dev]'

pre-commit: ## Install pre-commit hooks
	$(PRECOMMIT) install

fmt: ## Auto-format code (isort, black, ruff --fix)
	$(ISORT) .
	$(BLACK) .
	$(RUFF) check . --fix

format: fmt ## Alias for fmt

lint: ## Run linters (ruff, black --check, isort --check-only, pylint)
	$(RUFF) check .
	$(BLACK) --check .
	$(ISORT) --check-only .
	$(PYLINT) -rn -sn $(PACKAGES)

type: ## Run mypy type checks (non-fatal)
	$(MYPY) $(PACKAGES) || true

test: ## Run test suite (pytest)
	$(PYTEST)

cov: ## Run tests with coverage report
	$(PYTEST) --cov=aiteam --cov=apps --cov=agents_core --cov=memory --cov=orchestrator --cov=tools --cov-report=term-missing

check: lint test ## Lint and run tests

ci: check ## CI entrypoint (lint + tests)

run: ## Run Django development server (ASGI via runserver)
	$(MANAGE) runserver 0.0.0.0:8000

daphne: ## Run Daphne ASGI server on port 8001
	$(DAPHNE) -b 0.0.0.0 -p 8001 aiteam.asgi:application

celery: ## Start Celery worker
	$(CELERY) -A aiteam worker -l info

docs: ## Build Sphinx docs (HTML)
	$(SPHINXBUILD) -b html docs docs/_build/html

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov dist build docs/_build
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} +

env: ## Show important environment variables
	@echo "DJANGO_SETTINGS_MODULE=$${DJANGO_SETTINGS_MODULE:-aiteam.settings}"
	@echo "REDIS_URL=$${REDIS_URL:-not set}"
	@echo "NEO4J_URI=$${NEO4J_URI:-not set}"
	@echo "OLLAMA_HOST=$${OLLAMA_HOST:-not set}"
