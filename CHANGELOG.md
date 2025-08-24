# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## [Unreleased]
### Added
- Additional open-source docs (SECURITY.md, GitHub issue/PR templates)

### Changed
- Documentation refinements in README and Arc42

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
