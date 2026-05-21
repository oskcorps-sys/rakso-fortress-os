# SDD+ Phase 4 — Roadmap

**Status**: DRAFT
**Phase**: 4
**Target**: 2026-06-17 (4 sprints, ~4 weeks)
**Owner**: Oscar Franco (Operator/Architect)
**Reviewer**: Claude (Auditor + Implementer, dual-role workflow)

---

## Baseline (as of 2026-05-19)

- Tests passing: **118 / 118**
- Coverage: **92%** overall (≥85% on every Phase 3 module)
- Branch: `master` (Phase 3 merged, branches pruned)
- State: Phase 3 `COMPLETED`, `completed_phases: [0, 1, 2, 3]`
- Open advisories: zero (post item-2 Unicode fixes)

---

## Executive Summary

Phase 4 completes the harness and pushes SDD+ into **operability and distribution**.

The previous roadmap omitted the load-bearing piece: **file-pattern enforcement at commit time**. Without it, `AGENTS.yaml` declares which files each role may touch but nothing enforces it. That gap is the keystone of the harness and goes first.

Five items grouped into 4 sprints + 1 future:

1. **Sprint 1 (Harness closure)**: File-Pattern Enforcement + Git Integration
2. **Sprint 2 (Observability)**: Telemetry & Metrics
3. **Sprint 3 (Visibility)**: Web Dashboard
4. **Sprint 4 (Distribution)**: PyPI Packaging
5. **Future (Polish)**: Advanced Conflict Resolution

Coverage threshold stays at **≥85%** for every sprint — no relaxation.

---

## Items

### 1. File-Pattern Enforcement at Commit Time *(new — was missing from original roadmap)*
**Priority**: CRITICAL (closes the harness loop)
**Complexity**: Medium
**Effort**: ~2 days
**Value**: AGENTS.yaml goes from advisory to enforced — agents *cannot* commit files outside their role's allowed patterns.

**What it does**:
- `sdd install-hooks --role implementer|auditor` writes a git pre-commit hook
- Hook loads `AGENTS.yaml`, reads role's `allowed_file_patterns` / `forbidden_file_patterns`
- For each staged file, matches against patterns; rejects commit with a clear error if violated
- Fallback: if no role is set (env var `SDD_ROLE` or `.sdd-role` file), pre-commit is no-op (advisory mode)
- `sdd check-patterns --role X --files a.py b.yaml` for dry-run inspection

**Dependencies**: Phase 3 (AGENTS.yaml, agent schema)
**Blocks**: Git Integration (both touch pre-commit infrastructure)

---

### 2. Git Integration (auto-branch, auto-commit)
**Priority**: HIGH (operational glue)
**Complexity**: Medium
**Effort**: ~3 days
**Value**: SDD lifecycle events drive git events automatically.

**What it does**:
- `sdd new-phase` optionally creates `feature/phase-N` branch (flag-gated, default off in CI)
- `sdd audit` on APPROVED can auto-commit `AUDIT.yaml` with conventional message
- Reads git identity from workspace or environment
- Refuses to operate if working tree is dirty in ways that would lose data

**Dependencies**: Phase 3, File-Pattern Enforcement (pre-commit infrastructure shared)
**Blocks**: Telemetry (commit events feed metrics)

---

### 3. Telemetry & Metrics Emission
**Priority**: HIGH (needed before dashboard makes sense)
**Complexity**: Medium
**Effort**: ~2 days
**Value**: Operator can see SDD health across projects, over time.

**What it does**:
- Emit on phase transitions: `sdd.phase.transition` (phase, role, from_state, to_state, duration_ms)
- Emit on audits: `sdd.audit.result` (verdict, coverage_pct, test_count, finding_count)
- Local store: `.sdd-metrics/transitions.jsonl` + `.sdd-metrics/audits.jsonl` (JSONL, append-only)
- `sdd metrics show [--since DATE] [--phase N]` to query
- External backend (StatsD/Datadog/Prometheus) deferred — local only for Phase 4

**Dependencies**: Phase 3 state machine
**Blocks**: Dashboard

---

### 4. Web Dashboard
**Priority**: MEDIUM (nice-to-have, but not load-bearing)
**Complexity**: High
**Effort**: ~5 days
**Value**: Single pane of glass for workspace state.

**What it does**:
- Read-only HTTP server: `sdd dashboard --port 8888`
- Pages: workspace overview, project detail (phase timeline + audit history), metrics over time
- **Framework decision deferred to Sprint 3 kickoff** — candidates: FastAPI+HTMX (server-rendered, low complexity) vs FastAPI+React (richer, more deps). Default lean toward HTMX unless a strong reason emerges.
- No database, no auth — reads from `sdd.workspace.yaml`, `.sdd-metrics/`, `sdd/artifacts/`
- Coverage threshold: same 85% as other modules; UI integration tests via `httpx.AsyncClient`

**Dependencies**: Phase 3, Telemetry (data source)
**Blocks**: nothing

---

### 5. PyPI Packaging
**Priority**: MEDIUM (enables external users)
**Complexity**: Low
**Effort**: ~1.5 days
**Value**: `pip install sdd-plus` for anyone.

**Precondition**: **Verify `sdd-plus` name is available on PyPI before sprint kickoff.** If taken, choose alternate (`sdd-framework`, `sdd-harness`, etc.) and update `pyproject.toml`/branding consistently. Publishing the name is irreversible — confirm before any push.

**What it does**:
- Migrate to `src/sdd/` layout (current is flat `sdd/`)
- `pyproject.toml` already exists; tighten metadata (description, classifiers, README, keywords)
- Publish to TestPyPI first; smoke-test `pip install -i https://test.pypi.org/simple/ sdd-plus`
- Tag release `v0.1.0`, publish to live PyPI
- Add release/changelog process docs

**Dependencies**: Phases 1–4 complete
**Blocks**: nothing

---

### 6. Advanced Conflict Resolution *(deferred to post-Phase-4)*
**Priority**: LOW (only matters with concurrent multi-agent edits, which we don't have yet)
**Complexity**: High
**Effort**: ~4–5 days
**Value**: Handles concurrent phase edits — not needed until multi-team workflow is real.

Documented for future reference; not in Phase 4 scope.

---

## Sprint Plan

### Sprint 1: Harness closure (2026-05-20 → 2026-05-26)
Lock the harness, hook into git.

**Items**: File-Pattern Enforcement + Git Integration
**Deliverables**:
- `sdd/enforcement.py` — pattern matcher + pre-commit hook generator
- `sdd/git_integration.py` — branch / commit helpers (used by `new-phase` and `audit`)
- `sdd install-hooks`, `sdd check-patterns` CLI commands
- Updates to `new-phase` and `audit` for optional git integration
- Spec + Contract + Tests (≥85%)

**Exit criteria**:
- Implementer role cannot commit `sdd/artifacts/SPEC*.yaml` (pre-commit rejects)
- Auditor role cannot commit `src/**/*` (pre-commit rejects)
- `sdd new-phase --git` creates branch
- `sdd audit --git --auto-approve` commits the audit artifact
- All 118 + new tests pass, coverage ≥85% on new modules
- `sdd audit` verdict APPROVED for Phase 4 Sprint 1 increment

---

### Sprint 2: Observability (2026-05-27 → 2026-06-02)
Make state changes legible.

**Items**: Telemetry & Metrics Emission
**Deliverables**:
- `sdd/telemetry.py` — `MetricsCollector` + JSONL writers
- Wired into `state_machine.transition()` and `audit` command
- `.sdd-metrics/` directory created lazily
- `sdd metrics show` CLI
- Spec + Contract + Tests (≥85%)

**Exit criteria**:
- Running `sdd transition` writes one line to `.sdd-metrics/transitions.jsonl`
- Running `sdd audit` writes one line to `.sdd-metrics/audits.jsonl`
- `sdd metrics show --phase 4` returns structured output
- No-op when `.sdd-metrics/` directory not writable (fail-open)

---

### Sprint 3: Visibility (2026-06-03 → 2026-06-12)
Single pane of glass.

**Items**: Web Dashboard
**Deliverables**:
- Framework decision recorded in `sdd/artifacts/DECISION-PHASE4-DASHBOARD.md`
- `sdd/web/` — server + routes + templates/components
- `sdd dashboard` CLI
- Tests via `httpx.AsyncClient` (≥85%)

**Exit criteria**:
- `sdd dashboard --port 8888` serves a page listing all workspace projects
- Phase timeline visible for each project
- Audit history with pass/fail and coverage %
- Metrics chart (transitions per phase, audit verdict over time)

---

### Sprint 4: Distribution (2026-06-13 → 2026-06-17)
Make it installable.

**Items**: PyPI Packaging
**Deliverables**:
- `src/sdd/` layout migration
- Tightened `pyproject.toml` metadata
- TestPyPI publish
- Live PyPI publish (after name confirmed)
- README install section
- Tag `v0.1.0`

**Exit criteria**:
- `pip install sdd-plus` (or chosen name) in fresh venv works
- `sdd --version` returns `0.1.0`
- All previous sprints' tests run green from pip install
- Phase 4 final AUDIT.yaml APPROVED

---

## Timeline

| Sprint | Focus | Start | End | Days |
|--------|-------|-------|-----|------|
| 1 | Harness closure (enforcement + git) | 2026-05-20 | 2026-05-26 | 5 |
| 2 | Telemetry | 2026-05-27 | 2026-06-02 | 5 |
| 3 | Dashboard | 2026-06-03 | 2026-06-12 | 8 |
| 4 | PyPI | 2026-06-13 | 2026-06-17 | 3 |
| Future | Conflict Resolution | TBD | TBD | — |

---

## Success Metrics

Phase 4 is DONE when:

- All 4 sprints merged to master, each with its own audit APPROVED
- ≥85% coverage on every new module (no relaxation)
- Test count grows from **118** to an estimated **~155–170** (4 sprints × ~10–12 tests/sprint)
- File-pattern enforcement actively rejects forbidden commits in a smoke test
- Telemetry produces queryable JSONL after a synthetic phase run
- Dashboard renders the current workspace
- `pip install <chosen-name>` installs cleanly in a fresh venv
- Phase 4 final `AUDIT.yaml` verdict APPROVED, zero MEDIUM+ findings

---

## Open Decisions (resolve before each sprint)

| Decision | Sprint | Default if no input |
|----------|--------|---------------------|
| Dashboard framework (HTMX vs React) | 3 | HTMX (lower complexity) |
| PyPI package name | 4 | Verify `sdd-plus`; fallback `sdd-harness` |
| External telemetry backend | (deferred) | Local JSONL only for Phase 4 |
| `sdd install-hooks` opt-in vs default | 1 | Opt-in (explicit invocation) |

---

## Risks

- **PyPI name squat** — mitigated by pre-sprint check
- **Pre-commit hook conflicts** with existing user hooks — install a chained hook, don't overwrite
- **Dashboard scope creep** — strict read-only, no actions, no auth in Phase 4
- **Telemetry PII** — JSONL stores no user data beyond role string and timestamps; document this

---

## Next Step

→ Approve roadmap → create `PHASE_4_SPEC.yaml` + `PHASE_4_CONTRACT.yaml` (scope-locked for Sprint 1 only; later sprints get their own contracts when reached) → `sdd new-phase --role auditor` to enter Phase 4 DRAFT.
