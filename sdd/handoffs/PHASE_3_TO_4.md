# Handoff: Phase 3 -> Phase 4

- Completed: 2026-05-21T00:21:16Z
- Completed phases: [0, 1, 2, 3]
- Phase 3 audit: APPROVED (PHASE_3_AUDIT.yaml, 92% coverage, zero findings)

## Phase 3 delivered — Agent Harness

The harness frame is built. Roles are machine-readable and the audit loop is automated.

- `AGENTS.yaml` — authority matrix: per-role transitions, file patterns, constraints
- `AgentRoleSchema` / `AgentsConfigSchema` (Pydantic v2) validate it
- `transitions.py` loads roles from AGENTS.yaml, hardcoded fallback if absent
- `sdd audit` — 4-step loop (pytest, coverage >=85%, spec conformance, contract conformance)
- `sdd new-phase` — advances phase only when current is COMPLETED
- `sdd projects list/add/remove` + `sdd/workspace.py` — multi-project workspace
- 118 tests passing, 92% coverage

Post-merge cleanup also fixed a class of Windows Unicode bugs: every file I/O
now uses `encoding="utf-8"`, every `yaml.dump` uses `allow_unicode=True`, and CLI
output is ASCII-only. `acceptance_tests` entries may carry `kind: criterion` to
mark items verified by audit steps rather than by a test function.

## Carry-forward into Phase 4

The authority matrix is **declared but not enforced**. AGENTS.yaml says which
files each role may touch; nothing stops a misbehaving agent from committing
outside its lane. Phase 4 closes that gap.

- Phase 4 scope = roadmap Sprint 1: file-pattern enforcement (pre-commit hook)
  + git integration. See `PHASE_4_SPEC.yaml` / `PHASE_4_CONTRACT.yaml`.
- Roadmap Sprints 2-4 (telemetry, dashboard, PyPI) become Phases 5-7.
- Known stale data: earlier commits wrote a mojibake'd em-dash into some
  artifacts before the encoding fix landed. The fix prevents new corruption;
  pre-existing strings were cleaned by hand where found.
- Enforcement is denylist-only in Phase 4 (forbidden_file_patterns). Strict
  allowlist mode is explicitly deferred.
