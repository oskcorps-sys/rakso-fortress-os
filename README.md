# SDD+ — Specification-Driven Development Extended

Multi-agent AI orchestration framework with enforced spec-first development, independent audit gates, and production-ready conformance validation.

**Core principle**: Specifications are binding. Code follows spec, not vice versa. Audit is independent and impartial.

---

## Quick Start

### Prerequisites
- Python 3.11+
- `uv` (package manager) — install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Git

### Setup

```bash
# Clone or create project
git init sdd-project
cd sdd-project

# Copy all files from this scaffold into the directory

# Install dependencies
uv sync

# Verify setup
sdd --help
pytest tests/ -v --cov
```

### First Phase

```bash
# Codex reads AGENTS.md to understand implementer role
# Human reads CLAUDE.md to understand auditor role
# Human reads BEHAVIOR_NORMS.md for operational rules

# Start Phase 0
# Deliverable: repo exists, imports work, CI passes
```

---

## Architecture

```
sdd-project/
├── AGENTS.md                 # Implementer (Codex) role definition
├── CLAUDE.md                 # Auditor (Claude Code) role definition
├── README.md                 # This file
├── pyproject.toml            # Dependencies + build config
├── .gitignore
├── .pre-commit-config.yaml   # (Added in Phase 4)
├── .github/workflows/        # (Added in Phase 4)
│
├── sdd/                      # Main package
│   ├── __init__.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── sdd.py            # CLI (typer-based)
│   │
│   ├── validators/           # Validation code (Codex writes)
│   │   ├── __init__.py
│   │   ├── validate_contract.py
│   │   ├── validate_state_snapshot.py
│   │   └── contract_vs_code_check.py
│   │
│   ├── schemas/              # YAML schemas (pydantic models exported to JSON)
│   │   ├── contract.schema.yaml
│   │   ├── contract_review.schema.yaml
│   │   ├── state_snapshot.schema.yaml
│   │   ├── state_machine.schema.yaml
│   │   └── authority_matrix.schema.yaml
│   │
│   ├── artifacts/            # Working artifacts (version controlled)
│   │   ├── USER_STORY.yaml
│   │   ├── DECISIONS.yaml
│   │   ├── CONTRACT.yaml
│   │   ├── CONTRACT_REVIEW.yaml
│   │   ├── TEST_REPORT.yaml
│   │   ├── STATE_SNAPSHOT.yaml
│   │   └── PHASE_*_AUDIT.yaml (generated)
│   │
│   ├── skills/               # Modular skills (Codex writes)
│   │   ├── __init__.py
│   │   └── contract_generator/
│   │       ├── __init__.py
│   │       ├── SKILL.md
│   │       ├── skill.py
│   │       ├── input_schema.yaml
│   │       ├── output_schema.yaml
│   │       ├── examples/
│   │       └── tests/
│   │
│   ├── behavior/
│   │   └── BEHAVIOR_NORMS.md # Operational rules
│   │
│   ├── state-machine/
│   │   └── STATE_MACHINE.yaml # State definitions + transitions
│   │
│   └── logs/
│       └── .gitkeep           # Append-only audit logs (created at runtime)
│
├── tests/                    # Root test directory
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures
│   └── test_setup.py         # Bootstrap test
│
└── DECISIONS.md              # Technical decision log
```

---

## Phase Roadmap

| Phase | Deliverable | Codex (Builder) | Claude Code (Auditor) | Est. Duration |
|-------|-------------|-----------------|----------------------|---------------|
| 0 | Bootstrap | Create repo structure | Verify structure | 2-3h |
| 1 | Schemas + Validators | Write pydantic models + validators | Verify schema compliance + tests | 1d |
| 2 | State Machine + CLI | Implement STATE_MACHINE.yaml + sdd CLI | Verify state transitions + logs | 1d |
| 3 | First Skill | Implement contract_generator skill | Verify conformance ≥95% | 1d |
| 4 | CI + Conformance | Add pre-commit + GH Actions | Verify all gates work | 0.5d |
| 5 | Auditor Access | Authority matrix enforcement | Verify permissions enforced | 0.5d |
| 6 | Pilot Integration | Integrate with real project (NorthStar Hub) | Audit production readiness | 1d |

---

## Key Files to Read First

1. **AGENTS.md** — If you're the implementer (Codex)
2. **CLAUDE.md** — If you're the auditor (Claude Code)
3. **BEHAVIOR_NORMS.md** — Everyone (operational rules)
4. **DECISIONS.md** — Track technical choices per phase

---

## How It Works

### The Loop

```
1. Spec exists (USER_STORY.yaml + CONTRACT.yaml)
   ↓
2. Codex implements code + tests (feature/phase-N branch)
   ↓
3. Codex self-checks: pytest + validators pass locally
   ↓
4. Codex opens PR with link to CONTRACT.yaml
   ↓
5. Claude Code audits: 4-step loop (tests → schemas → conformance → decision)
   ↓
6. Claude Code fills PHASE_N_AUDIT.yaml
   ↓
7. If APPROVED: human approves merge → next phase starts
   If REJECTED: Codex fixes issues, pushes to same branch → back to step 5
   ↓
8. Once phase locked (git tag phase-N-locked), cannot regress
```

### Authority Split

**Codex writes**:
- `/sdd/validators/*` (validation code)
- `/sdd/tools/*` (CLI utilities)
- `/sdd/skills/*` (skill implementations)
- Feature branches (`feature/phase-N`)
- Test code

**Claude Code writes**:
- `/sdd/artifacts/PHASE_N_AUDIT.yaml` (audit report)
- `/sdd/artifacts/CONTRACT_REVIEW.yaml` (detailed feedback)
- `/sdd/artifacts/TEST_REPORT.yaml` (test summary)
- `/sdd/logs/audit.jsonl` (append-only audit log)

**Never**:
- Codex modifies audit artifacts
- Claude Code modifies implementation code
- Either modifies state transitions directly (use CLI)

---

## CLI Commands

```bash
# Once Codex implements Phase 2:
sdd validate contract                          # Validate CONTRACT.yaml
sdd validate state                             # Validate STATE_SNAPSHOT.yaml
sdd transition --from DRAFT --to REFINED      # Advance state
sdd snapshot                                   # Show current state
sdd log --phase 1 --agent codex                # View audit trail
```

---

## Testing

```bash
# Run all tests
pytest -v --cov

# Run specific phase tests
pytest tests/phase_1/ -v --cov

# Watch mode (requires pytest-watch)
ptw

# Coverage report (HTML)
pytest --cov --cov-report=html
open htmlcov/index.html
```

---

## Git Workflow

```bash
# Codex creates feature branch
git checkout -b feature/phase-N

# Codex commits CONTRACT first
git commit -m "PHASE N: Contract committed - [key spec points]"

# Codex implements + tests
git commit -m "PHASE N: [deliverable] - [context]"

# Codex pushes and opens PR
git push origin feature/phase-N

# (Claude Code audits in parallel)

# Once approved by Claude Code, human approves merge
git checkout main
git pull
git merge --no-ff feature/phase-N
git tag phase-N-locked

# Next phase starts from here
git checkout -b feature/phase-N+1
```

---

## Decisions to Confirm

Before starting Phase 0, confirm:

- [ ] **Pydantic v2** for schemas (type hints + validation)
- [ ] **Typer** for CLI (not click, not argparse)
- [ ] **Append-only logs** (git-style, immutable)
- [ ] **Phase-by-phase with human sign-off** (no auto-advance)
- [ ] **CI gates prevent merge** without audit green light
- [ ] **Repository**: GitHub private (or location of choice)

See `DECISIONS.md` for rationale.

---

## Contact & Maintenance

- **Maintainer**: Oscar (founder/CEO, ReguSense Inc.)
- **Current version**: 0.1.0 (Phase 0)
- **Last updated**: [date created]
- **Next review**: After Phase 1 audit complete

---

## License

MIT (for now — adjust as needed)

---

**Ready to start Phase 0? Read AGENTS.md + CLAUDE.md, then proceed.**
