# Pull Request

## Summary
Provide a clear summary of the change.

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactor
- [ ] CI/CD

## Checklist
- [ ] Tests added/updated and passing: `.venv/bin/pytest -q`
- [ ] Lint/format passing: `.venv/bin/ruff check .`, `.venv/bin/black --check .`, `.venv/bin/isort --check-only .`, `.venv/bin/pylint aiteam apps agents_core memory orchestrator tools`
- [ ] Docs updated: `README.md`, `docs/arc42/arc42.md`, `CHANGELOG.md`
- [ ] No secrets committed
- [ ] Adheres to restart policy (no Daphne restart for docs-only changes)

## How to test
Provide steps to validate the change.

## Related issues
Fixes #
Refs #
