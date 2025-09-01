# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## [Unreleased]
### Added
- Additional open-source docs (SECURITY.md, GitHub issue/PR templates)
- Sphinx Mermaid support (`sphinxcontrib-mermaid`) and MyST fence mapping for ```mermaid blocks
- Orchestrator-driven experts pipeline Celery task `run_experts_pipeline`
- API endpoint `POST /api/experts/run` with `?debug=1` and optional `&async=1`
- Tests covering experts pipeline (basic, debug, invalid JSON, invalid serializer)
- Cross-domain expert selection (IT + non-IT) with expanded catalog (e.g., legal, finance,
  marketing, HR, operations, healthcare, education, governance, research, data_science,
  ethics, localization, manufacturing, support)
- Tests for cross-domain experts and preservation of unknown LLM roles

### Changed
- Documentation refinements in README and Arc42
- Standardized Ruff usage across docs, Makefile, and CI (use `ruff check .` and `--fix` where appropriate); removed invalid flags.
- Documented optional `_debug` payload in initial `expert_update` WebSocket event and expanded related module docstrings.
- Experts pipeline executes Celery groups synchronously in-process for tests/local to avoid broker dependency; async scheduling only attempted when `REDIS_URL` is set
- LLM prompt for expert selection made cross-domain and unknown roles are preserved as-is

## [0.1.0] - 2025-08-24
### Added
- WebSocket streaming for Product Owner planning
  - Events: `po_plan_start`, `po_plan_step`, `po_plan_final`
- Agile Coach feedback event: `ac_feedback`
- Dynamic expert selection stubs with `expert_update` events
- REST API endpoints:
  - `GET /api/health`
  - `GET /api/memory/<agent>/history?limit=20`
- Short-term memory with shared in-memory fallback
- Long-term memory (Neo4j) minimal note upsert
- Tests: WebSocket streaming and API tests
- CI: GitHub Actions workflow

### Changed
- Ruff configuration migrated to new `lint.*` keys

[Unreleased]: https://github.com/your-org/aiteam/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/aiteam/releases/tag/v0.1.0
