# DECISIONS.md — Technical Decision Log

**Purpose**: Record why we chose certain tech/approaches. Rationale is more important than choice.

**Format**: One decision per entry. Include decision_id, title, options considered, chosen, rationale, phase, approver.

---

## Pre-Phase 0: Architecture Decisions

### DECISION-0001
**Title**: Pydantic v2 for schema validation  
**Date**: 2025-05-19  
**Phase**: 0 (applies to all)  
**Status**: APPROVED  
**Approver**: oscar  

**Options considered**:
1. Pydantic v2 (type hints + auto JSON Schema export + validation)
2. jsonschema (lightweight, pure JSON Schema)
3. pykwalify (YAML-native schema validation)

**Chosen**: Pydantic v2  

**Rationale**:
- Type hints make contracts explicit in code (IDE support, type checking)
- Auto-exports to JSON Schema (no manual sync needed)
- Runtime validation catches contract violations immediately
- Single source of truth: pydantic model = schema = code
- Integrates with typer CLI generation (Phase 2)
- Industry standard (FastAPI, Anthropic SDK use it)

**Tradeoff**: Adds ~10MB to deps; non-negligible for embedded use

**Related artifacts**: pyproject.toml, all schema files

---

### DECISION-0002
**Title**: Typer for CLI (not click, not argparse)  
**Date**: 2025-05-19  
**Phase**: 0 (applies to Phase 2+)  
**Status**: APPROVED  
**Approver**: oscar  

**Options considered**:
1. Typer (FastAPI-style, generates --help from docstrings)
2. Click (popular, mature, requires more code)
3. Argparse (stdlib, low-level)

**Chosen**: Typer  

**Rationale**:
- Docstrings → CLI help (DRY principle)
- Built on Click under the hood (proven)
- Autocomplete generation (uv shell integration)
- Type annotations → validation (pydantic under hood)
- Less boilerplate than Click or argparse
- Future: integrates with Claude Code's agentic CLI calls

**Tradeoff**: Less control than Click over argparse edge cases; acceptable for SDD+ scope

**Related artifacts**: sdd/tools/sdd.py, Phase 2 deliverables

---

### DECISION-0003
**Title**: Append-only logs (immutable audit trail)  
**Date**: 2025-05-19  
**Phase**: 0 (applies to all)  
**Status**: APPROVED  
**Approver**: oscar  

**Options considered**:
1. Append-only JSONL (git-like, immutable, replay-able)
2. Single JSON file (overwritten each time, simple but lossy)
3. Database with transaction log (overkill for this scope)

**Chosen**: Append-only JSONL  

**Rationale**:
- Immutable: cannot hide/modify past audits
- Replay-able: can reconstruct state at any point
- Git-friendly: diffs show exactly what happened
- Simple: just append a line, no schema complexity
- Auditable: every action timestamped, hashed
- Human-readable: one JSON object per line

**Tradeoff**: Requires "current" pointer (symlink/marker) to know active state; minor overhead

**Related artifacts**: /sdd/logs/audit.jsonl, STATE_SNAPSHOT.yaml

---

### DECISION-0004
**Title**: Phase-by-phase with human sign-off (no auto-advance)  
**Date**: 2025-05-19  
**Phase**: 0 (applies to all)  
**Status**: APPROVED  
**Approver**: oscar  

**Options considered**:
1. Auto-advance: phase N+1 starts when N is locked (fast, no human required)
2. Human sign-off: human reads PHASE_N_AUDIT, approves, merges (intentional, slow)
3. Hybrid: auto-advance if 0 findings, human sign-off if findings exist (complex)

**Chosen**: Human sign-off always  

**Rationale**:
- Ensures human maintains oversight (governance)
- Catches scope creep early (human sees what was built)
- Enforces "gates are real" (not automatic, deliberate approval)
- Aligns with SDD+ philosophy: spec is binding, audit is impartial, human decides
- Gives human 5-min reading time before next phase (checkpoint)
- If phases are bounded (AGENTS.md) and Codex is disciplined, approval is fast

**Tradeoff**: Slower overall timeline (human is bottleneck); acceptable for production rigor

**Related artifacts**: README.md, AGENTS.md, CLAUDE.md

---

### DECISION-0005
**Title**: Git-based state (no separate database)  
**Date**: 2025-05-19  
**Phase**: 0 (applies to all)  
**Status**: APPROVED  
**Approver**: oscar  

**Options considered**:
1. Git only: STATE_SNAPSHOT.yaml is source of truth, versioned
2. External DB: central state store, sync with git (drift risk)
3. Hybrid: git + DB with automated sync (complexity)

**Chosen**: Git only  

**Rationale**:
- Single source of truth: git history IS audit trail
- No sync issues: snapshot is committed, reflects reality
- Rollback is cheap: git revert to previous phase lock
- Auditable: every state change has commit hash + message
- Offline-friendly: no remote DB required
- Fits SDD+ philosophy: immutable gates, versioned contracts

**Tradeoff**: State is eventual-consistent (after push); not instant; acceptable for phase-based workflow

**Related artifacts**: sdd/artifacts/STATE_SNAPSHOT.yaml, phase locks

---

### DECISION-0006
**Title**: Python 3.11+ only (not 3.9, not 3.10)  
**Date**: 2025-05-19  
**Phase**: 0 (applies to all)  
**Status**: APPROVED  
**Approver**: oscar  

**Options considered**:
1. Python 3.11+ (modern features, type unions, match statements)
2. Python 3.9+ (broader compatibility, older syntax)

**Chosen**: Python 3.11+  

**Rationale**:
- Type hints with `X | Y` (not `Union[X, Y]`, cleaner)
- Match statements (pattern matching, cleaner control flow)
- Pydantic v2 fully optimized for 3.11+ (v2 backport to 3.9 is slower)
- SDD+ is new project (no legacy constraints)
- Codex/Claude Code assume modern syntax (aligned)

**Tradeoff**: Users with Python <3.11 must upgrade; acceptable for new project

**Related artifacts**: pyproject.toml, all .py files

---

### DECISION-0007
**Title**: GitHub private repo (or equivalent private git)  
**Date**: 2025-05-19  
**Phase**: 0  
**Status**: PENDING (awaiting Oscar confirmation)  
**Approver**: pending  

**Options considered**:
1. GitHub private (ubiquitous, strong history, CI integration)
2. GitLab private (self-hosted option, strong privacy)
3. Gitea (self-hosted, lightweight, air-gapped option)

**Chosen**: [Awaiting confirmation]  

**Rationale**: [Will fill based on Oscar's choice]  

**Related artifacts**: CI config, .github/workflows/, pre-commit setup

---

### DECISION-0008
**Title**: Coverage target: 80% (85%+ by Phase 3)  
**Date**: 2025-05-19  
**Phase**: 0  
**Status**: APPROVED  
**Approver**: oscar  

**Options considered**:
1. 100% coverage (ideal, unachievable, demoralized teams)
2. 80% coverage (good, practical, catches main paths)
3. 70% coverage (too loose, misses edge cases)

**Chosen**: 80% (85%+ by Phase 3)  

**Rationale**:
- 80% = main happy path + most constraints + key edge cases
- Phase 3+ raises to 85% (skill code is audited more strictly)
- Achievable without exhaustion (avoids coverage gaming)
- Leaves headroom for Phase 4+ integration tests (different tool)

**Tradeoff**: Not 100%; some paths untested. Acceptable if auditor reviews untested paths

**Related artifacts**: pyproject.toml, pytest configuration, all test files

---

### DECISION-0009
**Title**: Pydantic-yaml for schema serialization  
**Date**: 2025-05-19  
**Phase**: 1  
**Status**: APPROVED  
**Approver**: oscar  

**Options considered**:
1. pydantic-yaml (Pydantic models ↔ YAML, native)
2. PyYAML + manual mapping (manual, error-prone)
3. Marshmallow (schema library, overkill for YAML)

**Chosen**: pydantic-yaml  

**Rationale**:
- Bidirectional: Pydantic → YAML (serialization) + YAML → Pydantic (validation)
- Type-safe: uses same pydantic models as validators
- Consistent: single source of truth (pydantic model)
- Simple: one line to load YAML, get validated object

**Related artifacts**: sdd/schemas/*.yaml, sdd/validators/validate_contract.py

---

## Phase 0 Decisions (Bootstrap)

*None yet — will be added as Codex encounters decisions during Phase 0*

---

## Phase 1+ Decisions (To be filled)

*Phase 1 onward: log decisions here as they arise*

Example format:
```
### DECISION-1001
**Title**: [Decision title]
**Date**: YYYY-MM-DD
**Phase**: 1 (or which phase this applies to)
**Status**: APPROVED | PENDING | REJECTED
**Approver**: [who approved]

**Options considered**:
1. Option A (rationale)
2. Option B (rationale)

**Chosen**: Option X

**Rationale**: [Why Option X over others]

**Tradeoff**: [What we're giving up]

**Related artifacts**: [Files affected]
```

---

## Decision Appeal Process

If Codex or Claude Code disagrees with a decision:

1. **Document concern** in DECISIONS.md as comment under the decision
2. **Propose alternative** with full rationale
3. **Escalate to human** for arbitration
4. **Human decides** and updates DECISIONS.md with note
5. **Adjust workflow** if decision reversed (affects future phases)

Example:
```
# DECISION-0003 Appeal (Phase 2)
Codex concern: Append-only logs are getting large, slowing audit reads
Proposed alternative: Archive logs older than phase N-2
Human decision: Approved. Implement log rotation in Phase 4. Use gzip compression.
Updated: 2025-06-15 by oscar
```

---

## Summary Table

| ID | Title | Chosen | Phase | Status |
|----|-------|--------|-------|--------|
| 0001 | Pydantic v2 | Yes | 0+ | APPROVED |
| 0002 | Typer CLI | Yes | 0+ | APPROVED |
| 0003 | Append-only logs | Yes | 0+ | APPROVED |
| 0004 | Human sign-off | Yes | 0+ | APPROVED |
| 0005 | Git-based state | Yes | 0+ | APPROVED |
| 0006 | Python 3.11+ | Yes | 0+ | APPROVED |
| 0007 | Private repo (GitHub/etc) | Pending | 0 | PENDING |
| 0008 | Coverage 80%→85% | Yes | 0+ | APPROVED |
| 0009 | pydantic-yaml | Yes | 1+ | APPROVED |

---

**Last updated**: 2025-05-19 (Pre-Phase 0)  
**Next review**: After Phase 1 completion  
**Maintainer**: Oscar
