# Contributing to AITEAM

Thank you for your interest in contributing! This guide explains how to set up the development environment, follow the coding standards, run tests, and submit pull requests.

## Development Environment

- Python 3.10+
- Recommended: Docker for local Redis, Neo4j, and Ollama

Setup:
```
python -m venv .venv
. .venv/bin/activate
.venv/bin/pip install -e ".[dev,agents,docs]"
cp env.example .env
```

Optional services via Docker:
```
docker compose up -d redis neo4j ollama
```

Database migrations:
```
.venv/bin/python manage.py migrate
```

Run the app (preferred):
```
.venv/bin/daphne -b 127.0.0.1 -p 8001 aiteam.asgi:application
```

Open http://127.0.0.1:8001

## Restart Policy

- Do restart Daphne after code or template changes (e.g., `*.py`, `templates/`)
- Do NOT restart for documentation-only changes under `docs/` or `*.md` files

## Coding Standards

- PEP 8, PEP 257 (docstrings), type hints everywhere
- Keep functions short, focused, and side-effect free where possible
- Use meaningful names, avoid abbreviations
- Structure: separate core logic, models, API/services, and UI (Django + Bootstrap 5)

## Linting and Formatting

Run all with repository virtualenv executables:
```
.venv/bin/ruff check .
.venv/bin/black --check .
.venv/bin/isort --check-only .
.venv/bin/pylint aiteam apps agents_core memory orchestrator tools
```

## Tests

- Framework: `pytest`
- Target coverage: ≥ 90%
- Types of tests: unit, integration (AI, Neo4j), UI (Django test client)

Run tests:
```
.venv/bin/pytest -q
```

## Pre-commit Hooks

Install and enable hooks to ensure consistent quality:
```
.venv/bin/pre-commit install
.venv/bin/pre-commit run --all-files
```

Configured in `.pre-commit-config.yaml` to run Black, Ruff, Pylint, and tests where applicable.

## Documentation

- Update `docs/arc42/arc42.md` for architecture changes (Mermaid diagrams welcome)
- Keep `README.md` clear and current (features, WS protocol, API, setup)
- Changelog: follow SemVer in commits and PRs when applicable

## Commit Messages

- Use clear, descriptive messages
- Reference issues: `Fixes #123` or `Refs #123`
- Example: `feat(chat): stream PO planning steps with po_plan_* events`

## Pull Request Checklist

- [ ] Feature or fix is clearly described in PR
- [ ] Tests added/updated and passing (`.venv/bin/pytest -q`)
- [ ] Lint/format checks passing (Ruff, Black, isort, Pylint)
- [ ] Docs updated (`README.md`, `docs/arc42/arc42.md`)
- [ ] No secrets or credentials committed
- [ ] CI green

## Issue Triage

- Use labels: `bug`, `enhancement`, `documentation`, `good first issue`, `help wanted`
- Provide minimal reproduction, stack traces, and environment details

## Security

Please do not publicly disclose security issues. Open a private communication channel with maintainers (see repository contacts) or file a GitHub advisory if available. A maintainer will respond as soon as possible.

## Code of Conduct

By participating, you agree to abide by our `CODE_OF_CONDUCT.md`.
