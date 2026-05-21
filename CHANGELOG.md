# Changelog

All notable changes to SDD+ are documented here.

## [0.2.0] - 2026-05-21

LLM-agnostic refactor. SDD+ no longer assumes any specific AI provider.

### Changed
- **Executor field**: `AGENTS.yaml` roles now accept an optional `executor` field (default: `"any"`)
- **CLI `--executor` flag**: `sdd transition` and `sdd audit` accept `--executor` to record which LLM/human performed the action
- **Telemetry**: transition and audit events now include `executor` field
- **Schema**: `AgentRoleSchema` includes optional `executor` (default `"any"`)
- **Documentation**: README, description, and metadata rewritten to be fully LLM-agnostic
- **Version**: bumped to 0.2.0

### Removed
- All references to specific AI providers in documentation and metadata

---

## [0.1.0] - 2026-05-21

First public release. Seven phases of spec-driven development, fully audited.

### Added
- **State Machine** (Phase 2): 6-state lifecycle (DRAFT -> COMPLETED) with role-gated transitions
- **Schemas** (Phase 1): Pydantic v2 models for contracts, specs, audits, state snapshots
- **CLI** (Phase 2): `sdd` command with status, validate, transition, init, audit, new-phase
- **Agent Harness** (Phase 3): AGENTS.yaml authority matrix, AgentRoleSchema, automated audit loop
- **File-Pattern Enforcement** (Phase 4): git pre-commit hook enforcing AGENTS.yaml denylist rules
- **Git Integration** (Phase 4): `sdd install-hooks`, `sdd check-patterns`, `--git` flags on new-phase/audit
- **Telemetry** (Phase 5): JSONL event emission on transitions and audits, `sdd metrics show`
- **Web Dashboard** (Phase 6): FastAPI + Jinja2 + HTMX read-only dashboard at `sdd dashboard`
- **PyPI Packaging** (Phase 7): `pip install sdd-plus`

### Stats
- 244+ tests
- 91%+ coverage across all modules
- 7 phases, each independently audited with zero findings
- Zero external dependencies beyond Python stdlib + pydantic + typer + pyyaml + fastapi
