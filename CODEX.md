# CODEX.md — Self-Contained Implementer Briefing for Phase 2

> **Paste this entire file as your first prompt to OpenAI Codex CLI.**
> It contains everything you need: role, spec, protocol, instructions.
> You do NOT need to read any other files to start.

---

## PART 1: YOUR ROLE (from AGENTS.md)

You are the **Implementer Agent** in an SDD+ (Spec-Driven Development) dual-agent system.

**Your job:** Write code, tests, and contracts per specification.
**Your counterpart:** Claude Code (Auditor) — inspects your work, gates transitions.

### Authority Matrix

**You CAN write:**
- `sdd/state_machine/` — new code for this phase
- `sdd/cli/` — new code for this phase
- `sdd/schemas/` — modifications for carry-overs
- `sdd/validators/` — modifications for carry-overs
- `sdd/artifacts/examples/` — example artifacts
- `sdd/artifacts/PHASE_2_CONTRACT.yaml` — your contract
- `sdd/handoffs/PHASE_2_HANDOFF.md` — append status entries
- `tests/` — all test code
- `DECISIONS.md` — if you add a dependency

**You CANNOT write:**
- `sdd/artifacts/PHASE_2_SPEC.yaml` — Auditor's artifact
- `sdd/artifacts/PHASE_*_AUDIT.yaml` — Auditor's artifact
- `sdd/handoffs/PROTOCOL.md` — Auditor's artifact

### Key Rules
1. **Contract before code.** Write PHASE_2_CONTRACT.yaml FIRST.
2. **Tests must pass.** 0 failures, 0 skipped. ≥85% coverage on new code.
3. **Never modify audit artifacts.** Read PHASE_1_AUDIT.yaml, don't edit it.
4. **Escalate, don't workaround.** Disagree with spec? Flag it in HANDOFF, don't code around it.
5. **No scope creep.** Build exactly what the spec says, nothing more.

---

## PART 2: COMMUNICATION PROTOCOL

There is no chat. The repo IS the protocol.

### How to signal status
Append entries to `sdd/handoffs/PHASE_2_HANDOFF.md`. Format:

```
## [ISO8601] [CODEX] [STATUS_TAG]
Body with details.
```

**Tags you can emit:**
- `CONTRACT_DRAFT_READY` — contract written, waiting for auditor lock
- `IMPLEMENTING` — coding in progress
- `BLOCKED` — need clarification from spec
- `READY_FOR_AUDIT` — code + tests done (paste pytest output)
- `SPEC_REVISION_REQUEST` — you think the spec is wrong

### The Cycle
1. You write CONTRACT → signal `CONTRACT_DRAFT_READY` → **STOP**
2. Auditor reviews → signals `CONTRACT_LOCKED` in HANDOFF
3. You implement code + tests → signal `READY_FOR_AUDIT` → **STOP**
4. Auditor runs audit → `AUDIT_APPROVED` or `AUDIT_REJECTED`
5. If rejected: fix findings, re-signal `READY_FOR_AUDIT`

### Branch
Work on: `feature/phase-2` (already created from master)

---

## PART 3: PHASE 2 SPECIFICATION

**Title:** State Machine + CLI — SDD+ Workflow Engine
**Author:** Claude Code (Auditor)
**Date:** 2026-05-19

### What to build

The state machine that enforces SDD+ phase transitions, and the CLI
operators use to drive the workflow. This connects Phase 1 schemas/validators
into a usable tool.

### Success Criteria
- State machine with 6 states: DRAFT, REFINED, LOCKED, IMPLEMENTING, AUDITING, COMPLETED
- Transition table enforcing the Authority Matrix
- CLI commands: status, validate, transition, init (working end-to-end)
- STATE_SNAPSHOT.yaml updated automatically on every transition
- ≥85% test coverage on state_machine + cli
- Phase 1 carry-overs fixed (see Part 5)

### State Machine Spec

**States:**

| State | Meaning |
|-------|---------|
| DRAFT | Contract being authored, not committed |
| REFINED | Contract reviewed by Auditor, ready to lock |
| LOCKED | Contract immutable; implementation may begin |
| IMPLEMENTING | Code being written against locked contract |
| AUDITING | Implementer pushed PR; Auditor running audit loop |
| COMPLETED | Audit APPROVED; phase merged to main |

**Transitions:**

| From | To | Allowed Roles |
|------|----|--------------|
| DRAFT | REFINED | implementer, auditor |
| REFINED | LOCKED | **auditor only** (GATE) |
| LOCKED | IMPLEMENTING | implementer |
| IMPLEMENTING | AUDITING | implementer |
| AUDITING | COMPLETED | **auditor only** (GATE) |
| AUDITING | IMPLEMENTING | auditor (reject loop) |
| any | DRAFT | auditor (emergency reset) |

**Invariants:**
- Illegal transition raises `TransitionError` with role + state in message
- Every successful transition writes new `STATE_SNAPSHOT.yaml`
- Auditor-only transitions reject Implementer with explicit error

### CLI Spec

| Command | Description | Output |
|---------|-------------|--------|
| `sdd status` | Show current phase + state | Human-readable + optional `--json` |
| `sdd validate <path>` | Validate YAML artifact (uses Phase 1 validators) | Exit 0/1 + errors |
| `sdd transition <to_state> --role <role>` | Attempt state transition | Confirms new state OR error |
| `sdd init <name>` | Scaffold new SDD project | Creates dir + CONTRACT.yaml + STATE_SNAPSHOT.yaml |

### Files to Create

```
sdd/state_machine/__init__.py
sdd/state_machine/machine.py        — StateMachine class
sdd/state_machine/transitions.py    — ALLOWED_TRANSITIONS + TransitionError

sdd/cli/__init__.py
sdd/cli/main.py                     — Typer app entrypoint
sdd/cli/commands/__init__.py
sdd/cli/commands/status.py
sdd/cli/commands/validate.py        — wraps Phase 1 validators
sdd/cli/commands/transition.py
sdd/cli/commands/init.py

tests/test_state_machine.py          — 15+ tests
tests/test_cli.py                    — 8+ tests with CliRunner
```

### Constraints
- Use Typer for CLI (already in pyproject.toml)
- State machine is pure Python — no external state store (just YAML files)
- Every transition persists STATE_SNAPSHOT.yaml atomically (write .tmp + os.replace)
- CLI must work on Windows + Unix
- No new dependencies without DECISION-XXX entry in DECISIONS.md

### Acceptance Tests

1. `test_state_machine_legal_transition` — DRAFT → REFINED with role=auditor succeeds, STATE_SNAPSHOT updated
2. `test_state_machine_rejects_implementer_locking` — REFINED → LOCKED with role=implementer raises TransitionError
3. `test_cli_status_shows_current_state` — `sdd status` shows current state from STATE_SNAPSHOT.yaml
4. `test_cli_validate_invalid_exits_1` — `sdd validate <malformed.yaml>` exits 1 with error details
5. `test_cli_transition_rejects_wrong_role` — `sdd transition LOCKED --role implementer` exits 1
6. `test_state_snapshot_atomic_write` — transition writes .tmp + renames, file never half-written
7. `test_coverage_threshold` — ≥85% on sdd/state_machine and sdd/cli

---

## PART 4: EXISTING CODE CONTEXT

### Project Structure (what already exists)

```
sdd-template/
├── AGENTS.md                          # Your role (this is a summary)
├── CLAUDE.md                          # Auditor role
├── CODEX.md                           # THIS FILE
├── pyproject.toml                     # pydantic>=2.0, typer, pytest
├── sdd/
│   ├── __init__.py                    # __version__ = "0.1.0"
│   ├── schemas/
│   │   ├── __init__.py                # exports all 5 schemas
│   │   ├── base.py                    # BaseArtifact, ValidationResult, ErrorItem
│   │   ├── contract.py                # ContractSchema
│   │   ├── state.py                   # StateSnapshotSchema
│   │   ├── story.py                   # UserStorySchema
│   │   ├── spec.py                    # PhaseSpecSchema
│   │   └── audit.py                   # AuditResultSchema
│   ├── validators/
│   │   ├── validate_contract.py       # validate_contract(path_or_dict) → ValidationResult
│   │   └── validate_state.py          # validate_state(path_or_dict) → ValidationResult
│   ├── tools/
│   │   └── sdd.py                     # OLD CLI skeleton — replace or shim
│   ├── artifacts/
│   │   ├── CONTRACT.yaml              # Phase 0 template
│   │   ├── STATE_SNAPSHOT.yaml        # Current state
│   │   ├── PHASE_1_SPEC.yaml
│   │   ├── PHASE_1_CONTRACT.yaml
│   │   ├── PHASE_1_AUDIT.yaml         # DO NOT EDIT
│   │   └── PHASE_2_SPEC.yaml          # DO NOT EDIT
│   └── handoffs/
│       ├── PROTOCOL.md                # DO NOT EDIT
│       ├── PHASE_2_BRIEFING.md
│       └── PHASE_2_HANDOFF.md         # Append your status here
├── tests/
│   ├── test_schemas.py                # 8 tests (all passing)
│   └── test_validators.py             # 9 tests (all passing)
└── master branch: clean, Phase 1 merged
```

### Key imports you'll use

```python
# Phase 1 schemas
from sdd.schemas.contract import ContractSchema
from sdd.schemas.state import StateSnapshotSchema
from sdd.schemas.base import ValidationResult, ErrorItem

# Phase 1 validators
from sdd.validators.validate_contract import validate_contract
from sdd.validators.validate_state import validate_state
```

### StateSnapshotSchema fields (you'll read/write this)

```python
class StateSnapshotSchema(BaseArtifact):
    current_phase: int
    current_state: str          # DRAFT, REFINED, LOCKED, etc.
    last_updated: datetime
    completed_phases: List[int]
    metadata: Dict[str, Any]
    locked_at: Optional[datetime]
```

---

## PART 5: PHASE 1 CARRY-OVERS (fix these first, one commit)

These are findings from Phase 1 audit that must be resolved in Phase 2:

### F-P1-001: Create example artifacts
Create `sdd/artifacts/examples/valid_contract.yaml` and `invalid_contract.yaml`.
- Valid must pass `validate_contract()`
- Invalid must fail with at least 2 errors

### F-P1-003: Migrate Pydantic Config syntax
In ALL schema files (`base.py`, `contract.py`, `state.py`, `story.py`, `spec.py`, `audit.py`):

Replace:
```python
class Config:
    """Pydantic config."""
    extra = "allow"
```

With:
```python
model_config = ConfigDict(extra='allow')
```

Add `from pydantic import ConfigDict` to imports.

### F-P1-004: Fix deprecated datetime
In `sdd/schemas/base.py` line 42 and all test files:

Replace: `datetime.utcnow()`
With: `datetime.now(datetime.UTC)`

Import: `from datetime import datetime, UTC` (Python 3.11+)

### F-P1-005: Improve validate_state.py coverage
Add tests in `tests/test_validators.py` that exercise:
- The `yaml.YAMLError` branch in `validate_state()` (line 71)
- The generic `except Exception` branch in `validate_state()` (line 84)
Target: ≥80% individual coverage for validate_state.py

---

## PART 6: STEP-BY-STEP INSTRUCTIONS

### Step 1: Write the contract
Create `sdd/artifacts/PHASE_2_CONTRACT.yaml` with `status: DRAFT`.
Commit: `PHASE 2: Contract committed`
Append `CONTRACT_DRAFT_READY` to `sdd/handoffs/PHASE_2_HANDOFF.md`.
**STOP. Wait for CONTRACT_LOCKED before coding.**

### Step 2: Fix Phase 1 carry-overs (after CONTRACT_LOCKED)
Fix F-P1-001, F-P1-003, F-P1-004, F-P1-005.
Commit: `PHASE 2: Phase 1 carry-overs (F-P1-001/003/004/005)`

### Step 3: Implement state machine
Create `sdd/state_machine/` with machine.py and transitions.py.
Commit: `PHASE 2: State machine core`

### Step 4: Implement CLI
Create `sdd/cli/` with main.py and commands/.
Replace old `sdd/tools/sdd.py` with shim or update pyproject.toml entrypoint.
Commit: `PHASE 2: CLI commands`

### Step 5: Tests + coverage
Create `tests/test_state_machine.py` (15+ tests) and `tests/test_cli.py` (8+ tests).
Run: `python -m pytest tests/ -v --cov=sdd/state_machine --cov=sdd/cli --cov=sdd/schemas --cov=sdd/validators --cov-report=term-missing`
Must achieve ≥85% on new code.
Commit: `PHASE 2: Tests + coverage`

### Step 6: Signal done
Append `READY_FOR_AUDIT` to HANDOFF.md with full pytest output.
**STOP. Do not merge. Do not edit AUDIT files. Wait for Auditor.**

---

## PART 7: COMMIT MESSAGE FORMAT

```
PHASE 2: [deliverable] - [context]

[What changed and why]

Refs:
  Contract: sdd/artifacts/PHASE_2_CONTRACT.yaml
  Spec: sdd/artifacts/PHASE_2_SPEC.yaml

Tests: [X passed, 0 failed, Y% coverage]
```

---

## ENVIRONMENT NOTES

- Python: `python3` (Windows, Python 3.14)
- Tests: `python -m pytest` (not bare `pytest`)
- Atomic writes: use `os.replace(tmp_path, target_path)` — cross-platform
- Branch: `feature/phase-2` (already exists, checkout it)
- No `uv` — use `pip install` directly

---

**Start now. Read this document top to bottom, then begin with Step 1: write the contract.**
