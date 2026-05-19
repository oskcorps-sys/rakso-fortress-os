# PHASE 2 BRIEFING — for Codex (Implementer)

**From:** Claude Code (Auditor)
**To:** Codex
**Date:** 2026-05-19
**Status:** SPEC_READY — you may begin

---

## Mission

Build the **State Machine + CLI** layer on top of the schemas/validators
delivered in Phase 1. This is the runtime engine that turns SDD+ from a
collection of YAML specs into a working tool.

You also fix 4 carry-over findings from Phase 1 (see bottom).

---

## What to read FIRST (in order)

1. `AGENTS.md` — your role definition. Authority Matrix is non-negotiable.
2. `sdd/handoffs/PROTOCOL.md` — how we communicate.
3. `sdd/artifacts/PHASE_2_SPEC.yaml` — the spec you must implement.
4. `sdd/artifacts/PHASE_1_AUDIT.yaml` — the carry-over findings.

Do not start coding until you've read all four.

---

## What to deliver

### Step 1 — Write the contract
Create `sdd/artifacts/PHASE_2_CONTRACT.yaml` with `status: DRAFT`.
It must commit to:
- All `success_criteria` from PHASE_2_SPEC.yaml
- All `acceptance_tests` from PHASE_2_SPEC.yaml
- All 4 Phase 1 carry-overs
- Coverage ≥85% on `sdd/state_machine/` and `sdd/cli/`

Commit message: `PHASE 2: Contract committed`

Then append to `sdd/handoffs/PHASE_2_HANDOFF.md`:
```
## [TIMESTAMP] [CODEX] [CONTRACT_DRAFT_READY]
Contract written. Awaiting auditor review before LOCKED.
```

**STOP. Wait for `CONTRACT_LOCKED` from Auditor before writing code.**

### Step 2 — Fix Phase 1 carry-overs (one commit)
- **F-P1-001**: Create `sdd/artifacts/examples/valid_contract.yaml` and `invalid_contract.yaml`. Valid one must pass `validate_contract`; invalid one must fail with at least 2 errors.
- **F-P1-003**: Replace `class Config: extra = "allow"` with `model_config = ConfigDict(extra='allow')` in all schemas (`base.py`, `contract.py`, `state.py`, `story.py`, `spec.py`, `audit.py`). Import `ConfigDict` from pydantic.
- **F-P1-004**: Replace every `datetime.utcnow()` with `datetime.now(datetime.UTC)` in `sdd/schemas/base.py` and `tests/`.
- **F-P1-005**: Add tests in `tests/test_validators.py` that exercise the YAMLError branch AND the generic `except Exception` branch in `validate_state.py`. Target ≥80% individual coverage.

Commit message: `PHASE 2: Phase 1 carry-overs (F-P1-001/003/004/005)`

### Step 3 — Implement the state machine
Create:
- `sdd/state_machine/__init__.py`
- `sdd/state_machine/machine.py` — `StateMachine` class
- `sdd/state_machine/transitions.py` — `ALLOWED_TRANSITIONS` table + `TransitionError`

Requirements from `PHASE_2_SPEC.yaml > state_machine_spec`:
- 6 states: DRAFT, REFINED, LOCKED, IMPLEMENTING, AUDITING, COMPLETED
- Transition table enforces role-based authority (see spec)
- Every successful transition persists `STATE_SNAPSHOT.yaml` atomically (`.tmp` + rename)
- Illegal transition raises `TransitionError` with both role and target state in message

Commit message: `PHASE 2: State machine core`

### Step 4 — Implement the CLI
Create:
- `sdd/cli/__init__.py`
- `sdd/cli/main.py` — Typer `app`
- `sdd/cli/commands/status.py`
- `sdd/cli/commands/validate.py` (wraps Phase 1 validators)
- `sdd/cli/commands/transition.py`
- `sdd/cli/commands/init.py`

The existing `sdd/tools/sdd.py` is the OLD skeleton — replace it with a shim that imports from `sdd/cli/main.py`, or delete it and update `pyproject.toml` entrypoint to `sdd.cli.main:app`.

Make sure `pip install -e .` followed by `sdd --help` works.

Commit message: `PHASE 2: CLI commands`

### Step 5 — Tests + coverage
- `tests/test_state_machine.py` — 15+ tests covering every transition in `ALLOWED_TRANSITIONS` plus rejection cases for wrong roles.
- `tests/test_cli.py` — 8+ tests using `typer.testing.CliRunner`. Cover status, validate (valid + invalid), transition (legal + illegal role), init.
- Run: `pytest --cov=sdd/state_machine --cov=sdd/cli --cov=sdd/schemas --cov=sdd/validators --cov-report=term-missing`
- Coverage must be ≥85% on `sdd/state_machine` AND `sdd/cli`. Overall must not regress from 82%.

Commit message: `PHASE 2: Tests + coverage`

### Step 6 — Signal done
Append to `sdd/handoffs/PHASE_2_HANDOFF.md`:
```
## [TIMESTAMP] [CODEX] [READY_FOR_AUDIT]

All success criteria met.
Carry-overs F-P1-001/003/004/005 resolved.

pytest output:
<paste full pytest --cov output here>

Branch: feature/phase-2
Commits: <list>
```

Then **STOP**. Do not merge. Do not edit AUDIT files. Wait.

---

## What you MUST NOT do

- ❌ Edit `PHASE_2_SPEC.yaml` — that's the Auditor's artifact. If wrong, flag in HANDOFF.
- ❌ Edit `PHASE_1_AUDIT.yaml` — historical record, immutable.
- ❌ Skip the contract step. No code before `CONTRACT_LOCKED`.
- ❌ Merge `feature/phase-2` to `main`. Only Auditor merges.
- ❌ Add dependencies without a `DECISION-XXX` entry in `DECISIONS.md`.
- ❌ Reduce coverage below thresholds (85% on new code, 82% overall).
- ❌ Skip tests because "it works locally."

---

## What you SHOULD do when stuck

If a requirement is ambiguous or you believe the spec is wrong:
1. Stop coding.
2. Append `SPEC_REVISION_REQUEST` entry to `sdd/handoffs/PHASE_2_HANDOFF.md` with:
   - Which line of the spec is unclear/wrong
   - Why
   - Your proposed clarification
3. Wait for Auditor or Oscar to respond.

Better to pause for 5 minutes than to ship the wrong thing.

---

## Environment notes (Windows)

- Python: `python3` (Windows Store version). `python` alone may not work in some terminals.
- pytest: `python3 -m pytest`
- Atomic file writes: use `os.replace(tmp, target)` — works cross-platform.

---

Good luck. The Auditor will pick up your work at `READY_FOR_AUDIT`.
