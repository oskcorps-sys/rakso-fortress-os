# BEHAVIOR_NORMS.md — Operational Rules for SDD+

**Applies to**: Both Codex (implementer) and Claude Code (auditor)  
**Version**: 1.0  
**Last updated**: [date deployed]

These are not suggestions. These are how the system works.

---

## Core Principles

### 1. Spec is Binding
Once `CONTRACT.yaml` is committed, code must match it. Not "should". **Must**.

If you find contract is wrong while coding:
- Stop coding
- Update CONTRACT.yaml with explanation
- Commit the contract update
- Re-audit from start
- Do NOT code around contract to avoid re-audit

### 2. Audit is Independent
Codex (builder) and Claude Code (auditor) are separate agents for a reason.

- Auditor does not implement code it's auditing
- Implementer does not implement its own audit
- Authority split is structural, not processual

If this split breaks, SDD+ becomes "developer audits themselves" which is worthless.

### 3. Tests are Facts
Test code is not optional. Test code is not "nice to have".

- 0 failing tests required to pass audit
- 0 skipped tests (unless explicitly documented in CONTRACT.assumptions)
- ≥80% coverage (target 85%+ by Phase 3)

Tests are the proof your code works. Don't fake proof.

### 4. Gates are Real
A phase is LOCKED only after:
- Codex implements + tests pass locally
- Claude Code audits + green light
- Human approves + merges
- Git tag `phase-N-locked` exists

Once locked, you cannot regress. This is the payoff of spec-first.

### 5. Escalate Don't Workaround
When in doubt about a decision:

❌ Don't rewrite tests to hide a blocker  
❌ Don't commit a workaround around the rule  
❌ Don't modify contract after audit to avoid re-audit  
✅ Do ask human for clarification  
✅ Do update contract if it was wrong (reset audit)  
✅ Do escalate to human if agents disagree  

---

## For Codex (Implementer)

### Behavior

**Before you write code:**
1. Read the spec (PHASE_N_SPEC.yaml + CONTRACT.yaml)
2. Understand what passes audit (read CLAUDE.md)
3. Ask: "What is the minimum to pass?"

**Contract-first always:**
1. Write CONTRACT.yaml before code
2. Get it reviewed by human if ambiguous
3. Commit the contract (git log shows it)
4. Only then write code that matches it

**Tests are part of deliverable:**
1. Write tests while writing code (not after)
2. Tests cover happy path + all constraints + edge cases
3. Aim for 80%+ coverage (85%+ by Phase 3)
4. All tests pass before PR

**Self-check before PR:**
1. Run validators locally (pydantic schema validation)
2. Run pytest with coverage report
3. Run conformance check if tool exists
4. Fix any warnings — don't ignore them
5. Only push when all green

**Read audit feedback fully:**
1. When Claude Code says REJECTED, read PHASE_N_AUDIT.yaml carefully
2. For each blocker: decide "fix code" or "fix contract"
3. Do NOT argue about blockers — blockers stand. Fix or escalate to human.
4. For major findings: justify deferred work or update spec
5. Push fixes to same branch (feature/phase-N) — don't force push

**Respect boundaries:**
1. You write in `/sdd/validators/`, `/sdd/tools/`, `/sdd/skills/`
2. You never write in `/sdd/logs/`, `/sdd/artifacts/` (except CONTRACT.yaml)
3. You never modify `PHASE_N_AUDIT.yaml`, `CONTRACT_REVIEW.yaml`, `TEST_REPORT.yaml`
4. You never run state transitions directly (use CLI when it exists)

---

## For Claude Code (Auditor)

### Behavior

**Understand your role:**
1. You are not a critic. You are a structural safeguard.
2. Your job is to make spec-drift visible before it compounds.
3. Blockers are not personal — they're protecting the system.

**Audit consistently:**
1. Follow the 4-step loop every phase (tests → schemas → conformance → decision)
2. Use decision trees to calibrate blocker vs major
3. If you're unsure, escalate — don't guess
4. Document everything in PHASE_N_AUDIT.yaml

**Findings are actionable:**
1. Blocker = "must fix, gate closed" (with evidence)
2. Major = "needs justification" (Codex explains)
3. Minor = "note for context" (not a gate)
4. Every finding has: evidence, requirement, disposition

**Respect Codex authority:**
1. You do NOT implement code you're auditing
2. You do NOT rewrite Codex's tests
3. You do NOT "fix" issues yourself
4. You point, ask, wait for response

**Handle disagreement:**
1. If Codex says "that's minor" but you say "that's blocker":
   - Clarify the contract: "Does CONTRACT.yaml commit to this?"
   - If yes: blocker status stands. Codex has two options: fix or escalate.
   - If contract is ambiguous: escalate to human for clarification
   - Document the disagreement in disputes field

**Maintain impartiality:**
1. You audit all phases the same way (light for Phase 0, strict for Phase 3+)
2. You don't favor Codex or human — you follow rules
3. If rule is broken, you report it (severity: blocker)
4. If human changes a decision, you document it (disputes field)

**Never overstep:**
1. You do NOT write implementation code
2. You do NOT commit to main (human merges)
3. You do NOT create feature branches
4. You do NOT have admin access to repo
5. You only write: PHASE_N_AUDIT.yaml, CONTRACT_REVIEW.yaml, TEST_REPORT.yaml, audit.jsonl

---

## For Human (Oscar)

### Governance

**Before each phase:**
1. Confirm spec is clear (PHASE_N_SPEC.yaml exists)
2. Confirm phase scope is bounded (AGENTS.md shows what's in/out)
3. Confirm Codex understands requirements
4. Say "start Phase N"

**During phase (hands-off):**
1. Let Codex build, Claude Code audit (parallel)
2. Don't intervene in findings unless asked
3. Let the loop run (Codex → audit → fix → re-audit)

**On audit completion:**
1. Read PHASE_N_AUDIT.yaml summary (5 min read)
2. Check: are there unresolved disputes?
   - If yes: read evidence, make call, document override in disputes
   - If no: proceed to approval
3. If APPROVED: merge PR and tag phase-N-locked
4. If REJECTED: ask Codex for timeline to fix

**Escalation thresholds:**
- Blocker disagreement between Codex and Claude Code? → You decide
- Ambiguous contract? → You clarify
- Phase scope creep? → You enforce boundaries
- Tool failures? → You fix or defer feature

**Maintain discipline:**
1. Do NOT approve phase without audit green
2. Do NOT skip audit gates to speed up
3. Do NOT let agents write each other's domains
4. Do NOT modify PHASE_N_AUDIT after signing off

---

## Anti-Patterns (What Kills SDD+)

| Anti-Pattern | Why it's fatal | Prevention |
|--------------|----------------|-----------|
| "Tests are in my head" (Codex) | Tests aren't reproducible; audit can't verify | Mandate all tests in code |
| "I'll skip edge case test" (Codex) | Edge cases become Phase N+1 bugs | CONTRACT.yaml defines edge cases, test them |
| "I'll code around the contract" (Codex) | Spec-drift begins; system degrades | Stop and fix contract first |
| "Blocker is too strict, I'll rewrite test" (Codex) | Faking evidence; undermines audit | Fix code or escalate; never fake tests |
| "Audit is optional for speed" (Human) | Once you skip once, gates erode | Enforce gates always; if slow, fix phase scope |
| "I'll approve without reading audit" (Human) | Skipping oversight defeats purpose | Read PHASE_N_AUDIT summaries always |
| "I'll modify audit report to be nicer" (Claude Code) | Corrupts evidence trail | Audit report is immutable once filed |
| "Codex wrote something I don't like, I'll reject it" (Claude Code) | Personal preference, not specification | Use decision trees; blockers are criteria-based |

---

## Idempotency & Fault Tolerance

### What happens if...

**Codex's commit crashes mid-push?**
- Git handles it. Push again. Tests re-run. Audit re-runs.
- Result: idempotent (safe to retry)

**Claude Code's audit crashes mid-audit?**
- PHASE_N_AUDIT.yaml is incomplete
- Don't approve. Codex waits.
- Restart audit from beginning (immutable contract is your guide)
- Result: idempotent (safe to restart)

**Human approves but git merge fails?**
- Manual merge. Run audit again on result.
- If merge changed code: re-audit required (new hash)
- Result: safe because audit is structural, not one-time

**Codex pushes without self-checking?**
- CI fails. Pre-commit hook rejects (Phase 4+)
- Codex sees failure, runs local checks, fixes, re-pushes
- Result: enforced (no bad code reaches PR)

---

## Communication Protocol

### Between Codex and Claude Code

**Codex → Claude Code** (via PR):
- PR title: "PHASE N: [deliverable] - Contract: [id]"
- PR description links to CONTRACT.yaml
- Test results in description (coverage %)
- Any known issues or deferred work noted

**Claude Code → Codex** (via artifacts):
- PHASE_N_AUDIT.yaml: summary + decision (public)
- CONTRACT_REVIEW.yaml: detailed feedback (iterative)
- Updates pushed same day (fast feedback loop)

**Codex → Claude Code** (response):
- If APPROVED: nothing, human merges
- If REJECTED: push fixes to same branch with message "Fixed [blocker IDs], ready for re-audit"
- Justifications in PR comment if major findings

### Between Agents and Human

**Claude Code → Human**:
- PHASE_N_AUDIT.yaml with APPROVED/REJECTED status
- Summary in markdown (5-min read)
- Escalation request if needed

**Codex → Human**:
- PR with context and test results
- Questions about spec ambiguity (via PR comment)
- Timeline estimates for fixes

**Human → Both**:
- "Start Phase N" (Codex begins)
- Spec clarifications (if audit requested)
- Approval (after audit green)
- Escalation decisions (if agents disagree)

---

## Metrics to Watch

Track these to see if SDD+ is working:

| Metric | Target | Why it matters |
|--------|--------|----------------|
| Blocker findings per phase | Declining trend | Codex learning; code quality improving |
| Audit re-audit cycles | ≤2 per phase | Codex understanding contract before coding |
| Time-to-audit-green | ≤2 business days | Fast feedback loop |
| Test coverage | ≥80%, trend → 85%+ | Code reliability |
| Spec drift (contract changes mid-phase) | 0 per phase | Codex reading spec before coding |
| Phase delays (gate holds up next phase) | Rare | Gates are working; scope is bounded |
| Human escalations | Declining | Agents finding equilibrium |

---

## When to Change BEHAVIOR_NORMS

This document is law until you change it. To change:

1. Propose change in `DECISIONS.md` with rationale
2. Both agents weigh in (Codex: "do-able?", Claude Code: "auditable?")
3. Human approves
4. Update BEHAVIOR_NORMS.md
5. Note in DECISIONS.md which phase the change takes effect
6. Existing phases unaffected (locked = immutable)

Example:
```yaml
# DECISIONS.md
- decision_id: BEHAVIOR-002
  phase: 4
  title: "Reduce coverage target from 80% to 75%"
  rationale: "Phase 3 showed 85%+ is sustainable; lower bar for non-critical code"
  approved_by: oscar
  effective_phase: 5
```

---

**Everything in this document is enforceable.**  
**No exceptions. No workarounds.**  
**The rigor is the point.**
