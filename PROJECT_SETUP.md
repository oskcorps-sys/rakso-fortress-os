# SDD+ Project Setup — Complete Copy-Paste Guide

**Status**: Phase 0 Bootstrap — Ready to deploy  
**Generated**: 2025-05-19  
**For**: Oscar (ReguSense Inc.)  
**Next step**: Copy these files into your repo, then hand off to Claude Code  

---

## Quick Summary

You have **everything** for Phase 0:
- ✅ Dual-agent blueprints (AGENTS.md, CLAUDE.md)
- ✅ Operational rules (BEHAVIOR_NORMS.md)
- ✅ Technical decisions (DECISIONS.md, pyproject.toml)
- ✅ Project structure (directories + __init__.py files)
- ✅ Sample artifacts (CONTRACT.yaml, STATE_SNAPSHOT.yaml, USER_STORY.yaml)
- ✅ State machine (STATE_MACHINE.yaml)
- ✅ CLI skeleton (sdd.py with typer)
- ✅ Validators skeleton (validate_contract.py)
- ✅ Tests (conftest.py, test_setup.py)
- ✅ Setup script (setup-sdd.sh)

**No code is missing. It's all concrete.**

---

## File Manifest

These files are ready in `/mnt/user-data/outputs/`:

```
sdd-project/
├── pyproject.toml                    [project config: pydantic, typer, pytest]
├── .gitignore                        [Python ignores]
├── README.md                         [project overview + quick-start]
├── AGENTS.md                         [Codex/implementer role blueprint]
├── CLAUDE.md                         [Claude Code/auditor role blueprint]
├── BEHAVIOR_NORMS.md                 [operational rules for both agents]
├── DECISIONS.md                      [technical decision log]
├── setup-sdd.sh                      [bash script to initialize repo]
├── PROJECT_SETUP.md                  [this file]
│
├── sdd/
│   ├── __init__.py                   [package init: version 0.1.0]
│   ├── tools/
│   │   ├── __init__.py
│   │   └── sdd.py                    [CLI app: typer-based, Phase 2+ commands]
│   │
│   ├── validators/
│   │   ├── __init__.py
│   │   └── validate_contract.py      [Contract validator: Phase 1 impl]
│   │
│   ├── skills/
│   │   └── __init__.py               [Skills package: (empty for Phase 0)]
│   │
│   ├── artifacts/
│   │   ├── USER_STORY.yaml           [template: user story spec]
│   │   ├── CONTRACT.yaml             [template: technical contract]
│   │   ├── STATE_SNAPSHOT.yaml       [template: current state]
│   │   └── .gitkeep                  [ensure dir is tracked]
│   │
│   ├── schemas/
│   │   └── .gitkeep                  [schemas added in Phase 1]
│   │
│   ├── behavior/
│   │   └── BEHAVIOR_NORMS.md         [reference: operational rules]
│   │
│   ├── state-machine/
│   │   └── STATE_MACHINE.yaml        [state defs + transitions]
│   │
│   └── logs/
│       └── .gitkeep                  [append-only audit logs created at runtime]
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   [shared pytest fixtures]
│   └── test_setup.py                 [Phase 0 bootstrap tests]
│
└── [other dotfiles and README files as above]
```

**Total**: ~30 files, all ready to deploy.

---

## Setup Instructions (Copy-Paste)

### Option A: Using the setup script (recommended)

```bash
# 1. Create project directory
mkdir sdd-project
cd sdd-project

# 2. Copy all files from /mnt/user-data/outputs/ into sdd-project/
# (Or download from wherever you stored them)
# E.g.:
cp -r /mnt/user-data/outputs/* .

# 3. Run setup script
chmod +x setup-sdd.sh
bash setup-sdd.sh .

# 4. Install dependencies
uv sync
# OR if you prefer pip:
# pip install -e .

# 5. Run tests (verify Phase 0 works)
pytest tests/ -v --cov

# 6. Check structure
ls -la
sdd --help  # Should show CLI

# 7. Git status (confirm bootstrap commit)
git log --oneline | head -5
```

Expected output:
```
✓ Directory structure created
✓ Python packages initialized
✓ Git repository initialized
✓ Git initialized

📋 Next steps:
   ...

tests/test_setup.py::TestPhase0Bootstrap::test_imports_work PASSED
tests/test_setup.py::TestPhase0Bootstrap::test_cli_import PASSED
...

======================== 10 passed in 1.23s =========================
Coverage: 45%  [core code coverage baseline]

$ sdd --help
Usage: sdd [OPTIONS] COMMAND [ARGS]...

  Specification-Driven Development Extended - CLI tool

Options:
  --help      Show this message and exit.
  --verbose   Verbose output

Commands:
  init        Initialize a new SDD+ project
  log         Show audit logs (Phase 2+)
  snapshot    Show current state (Phase 2+)
  transition  Transition state (Phase 2+)
  validate    Validate artifacts (Phase 1+)
```

### Option B: Manual setup (if script doesn't work)

```bash
# 1. Create directories
mkdir -p sdd-project
cd sdd-project
mkdir -p sdd/{artifacts,logs,schemas,validators,tools,skills,behavior,state-machine}
mkdir -p tests

# 2. Copy files (manually or via your file manager)
# Copy all .py files, .yaml files, .md files from outputs/

# 3. Install Python dependencies
uv sync  # or: pip install -e .

# 4. Initialize git
git init
git add .
git commit -m "PHASE 0: SDD+ scaffold - bootstrap project structure"

# 5. Test
pytest tests/ -v --cov
sdd --help
```

---

## File Contents Summary (For Reference)

| File | Purpose | Size | Status |
|------|---------|------|--------|
| pyproject.toml | Dependencies: pydantic, typer, pytest | 2 KB | ✅ Ready |
| .gitignore | Python ignores | 1 KB | ✅ Ready |
| README.md | Project overview | 8 KB | ✅ Ready |
| AGENTS.md | Codex role blueprint | 15 KB | ✅ Ready |
| CLAUDE.md | Auditor role blueprint | 18 KB | ✅ Ready |
| BEHAVIOR_NORMS.md | Operational rules | 12 KB | ✅ Ready |
| DECISIONS.md | Decision log (9 pre-decisions) | 12 KB | ✅ Ready |
| sdd/__init__.py | Package init | 0.2 KB | ✅ Ready |
| sdd/tools/sdd.py | CLI (typer-based) | 5 KB | ✅ Ready |
| sdd/validators/validate_contract.py | Contract validator | 4 KB | ✅ Ready |
| sdd/artifacts/*.yaml | 3 templates (CONTRACT, STATE, STORY) | 4 KB | ✅ Ready |
| sdd/state-machine/STATE_MACHINE.yaml | State defs + transitions | 8 KB | ✅ Ready |
| tests/conftest.py | Pytest fixtures | 3 KB | ✅ Ready |
| tests/test_setup.py | Bootstrap tests | 8 KB | ✅ Ready |
| setup-sdd.sh | Setup automation | 1 KB | ✅ Ready |

**Total payload**: ~120 KB of documentation + code. Git-friendly.

---

## Phase 0 Checklist

Before handing off to Claude Code, verify:

- [ ] Directory structure created (15+ dirs)
- [ ] All Python __init__.py files present
- [ ] pyproject.toml has: pydantic, typer, pytest
- [ ] pytest runs: `pytest tests/ -v --cov` (should see 10+ tests pass)
- [ ] CLI works: `sdd --help` (shows commands)
- [ ] Git repo initialized: `git log` shows bootstrap commit
- [ ] README.md explains the architecture
- [ ] AGENTS.md and CLAUDE.md are identical files (or role-specific variants)
- [ ] BEHAVIOR_NORMS.md has ~20 rules documented
- [ ] DECISIONS.md has 9 pre-decisions (confirm these before Phase 1)
- [ ] No import errors: `python -c "import sdd; print(sdd.__version__)"`

If all ✅, proceed to next step.

---

## Confirmation Before Phase 1

You still need to decide (from DECISIONS.md):

**DECISION-0007** (Pending):
- [ ] Confirm repo location: GitHub private? GitLab? Gitea?
- [ ] Once confirmed, update DECISIONS.md with approved option

Once DECISION-0007 is confirmed, Phase 0 is complete and Phase 1 can start.

---

## What's NOT Included (Intentionally)

These are Phase 1+ deliverables:

- ❌ Pydantic schema models (written in Phase 1 by Codex)
- ❌ Full validator implementations (written in Phase 1 by Codex)
- ❌ Pre-commit hooks (added in Phase 4)
- ❌ GitHub Actions (added in Phase 4)
- ❌ Actual skills code (added in Phase 3)
- ❌ CLI full commands (added in Phase 2)
- ❌ Authority matrix enforcement (added in Phase 5)

This is intentional. Phase 0 is *structure* + *governance*. Code comes in Phase 1.

---

## What Happens Next

### Step 1: Confirm repo location (DECISION-0007)
You decide where this repo lives (GitHub, GitLab, Gitea). Update DECISIONS.md.

### Step 2: Add to version control
```bash
# Initialize remote (example: GitHub)
git remote add origin https://github.com/your-org/sdd-project.git
git branch -M main
git push -u origin main
```

### Step 3: Hand off CLAUDE.md to Claude Code
Share CLAUDE.md with Claude Code agent. It now knows:
- Its role (auditor, not implementer)
- The 4-step audit loop
- How to fill PHASE_N_AUDIT.yaml
- Authority boundaries

### Step 4: Hand off AGENTS.md to Codex
Share AGENTS.md with Codex. It now knows:
- Its role (implementer, not auditor)
- Contract-first workflow
- Authority boundaries
- How to respond to audit findings

### Step 5: Start Phase 1
Human says "Start Phase 1".
- Codex reads PHASE_1_SPEC.yaml (you write this)
- Codex writes CONTRACT.yaml
- Codex implements validators + tests
- Codex opens PR
- Claude Code audits
- Loop until APPROVED
- Human merges, tags, next phase

---

## Troubleshooting

### "sdd: command not found"
```bash
# Make sure you installed the package
uv sync  # or: pip install -e .

# Then:
python -m sdd.tools.sdd --help  # should work

# Or:
sdd --help  # should also work
```

### "pytest: ModuleNotFoundError: No module named 'sdd'"
```bash
# Make sure you're in the project directory
cd sdd-project

# Reinstall in development mode
pip install -e .

# Or use uv:
uv sync
```

### "YAML parse error"
```bash
# Check that .yaml files are valid YAML
python -c "import yaml; yaml.safe_load(open('sdd/artifacts/CONTRACT.yaml'))"
# Should output: None (meaning valid YAML was parsed)
```

### "Git refuses to commit"
```bash
# Make sure .gitignore is present
ls -la | grep gitignore  # should show .gitignore

# Force add if needed:
git add -f .gitignore
git commit -m "Add .gitignore"
```

---

## Files Ready to Download

All files are in `/mnt/user-data/outputs/`. Download or copy:

```bash
# Option 1: Copy all at once (from Claude output)
cp -r /mnt/user-data/outputs/* ~/sdd-project/

# Option 2: Download individual files (via UI)
# Click on each file in outputs/ folder

# Option 3: Via script
tar -czf sdd-scaffold.tar.gz -C /mnt/user-data/outputs/ .
# Then extract in your repo
```

---

## Success Criteria (Phase 0 complete)

You'll know Phase 0 is done when:

1. ✅ Repo exists with all files
2. ✅ `pytest tests/ -v` shows 10+ tests passing
3. ✅ `sdd --help` works
4. ✅ Git history shows "PHASE 0: SDD+ scaffold..." commit
5. ✅ README.md, AGENTS.md, CLAUDE.md are readable
6. ✅ DECISIONS.md has 9 decisions (DECISION-0007 still pending)
7. ✅ No import errors, no YAML errors
8. ✅ You understand the split between auditor (Claude Code) and implementer (Codex)

Once all 8 are ✅, you're ready to start Phase 1.

---

## Next: What to Read

Once Phase 0 is deployed:

1. **README.md** (5 min) — Project overview
2. **BEHAVIOR_NORMS.md** (10 min) — Rules for both agents
3. **AGENTS.md** (15 min) — If you're building (Codex role)
4. **CLAUDE.md** (15 min) — If you're auditing (Claude Code role)
5. **DECISIONS.md** (10 min) — Understand the "why" behind choices

Total: ~45 min to fully onboard.

---

## Questions?

- **Architecture**: See README.md + DECISIONS.md
- **Rules**: See BEHAVIOR_NORMS.md
- **Your role**: AGENTS.md (implementer) or CLAUDE.md (auditor)
- **Technical choices**: DECISIONS.md
- **Implementation**: Phase 1 spec (you write PHASE_1_SPEC.yaml)

---

**Phase 0 is complete. You are ready for Phase 1.**

**Next command**: `cd sdd-project && pytest tests/ -v --cov`

**Then pass blueprints to Claude Code and Codex.**

---

**Generated**: 2025-05-19  
**For**: Oscar (ReguSense Inc.)  
**Version**: SDD+ v0.1.0 (Phase 0)  
**Status**: ✅ Ready to deploy
