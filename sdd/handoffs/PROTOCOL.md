# SDD+ Dual-Agent Communication Protocol

**Version:** 1.0
**Created:** 2026-05-19
**Owner:** Claude Code (Auditor)

---

## Roles & Boundaries

| Role | Agent | Reads | Writes |
|------|-------|-------|--------|
| **Implementer** | Codex | Everything | `sdd/` (except artifacts/), `tests/`, `sdd/artifacts/PHASE_N_CONTRACT.yaml` |
| **Auditor** | Claude Code | Everything | `sdd/artifacts/PHASE_N_SPEC.yaml`, `sdd/artifacts/PHASE_N_AUDIT.yaml`, `sdd/handoffs/*` |
| **Human** | Oscar | Everything | Anything (final word) |

**Hard rules:**
- Implementer NEVER edits `*_SPEC.yaml` or `*_AUDIT.yaml`.
- Auditor NEVER edits production code or tests.
- Either may propose changes to the other's domain via `sdd/handoffs/PHASE_N_HANDOFF.md`.

---

## Communication Channel: Git + Handoff Files

There is no chat, no Slack, no email. The repo IS the protocol.

```
sdd/handoffs/
├── PROTOCOL.md                  # This file (read once, follow always)
├── PHASE_N_BRIEFING.md          # Auditor → Codex: what to do in phase N
├── PHASE_N_HANDOFF.md           # Bidirectional log: status, blockers, READY_FOR_AUDIT
└── PHASE_N_AUDIT_NOTES.md       # Auditor's working notes (optional)
```

---

## The Cycle

```
1. AUDITOR    writes PHASE_N_SPEC.yaml + PHASE_N_BRIEFING.md
   → commits to main
                            ▼
2. CODEX      reads SPEC + BRIEFING
              writes PHASE_N_CONTRACT.yaml (status=DRAFT)
              commits to feature/phase-N
              leaves "CONTRACT READY FOR REVIEW" in HANDOFF.md
                            ▼
3. AUDITOR    reviews contract vs spec
              if OK → marks state REFINED → LOCKED in STATE_SNAPSHOT
              leaves "CONTRACT LOCKED — implement" in HANDOFF.md
                            ▼
4. CODEX      implements code + tests against LOCKED contract
              keeps coverage above target
              leaves "READY FOR AUDIT" in HANDOFF.md with pytest output pasted
                            ▼
5. AUDITOR    runs audit loop (4 steps from CLAUDE.md)
              writes PHASE_N_AUDIT.yaml
              APPROVED → merges feature/phase-N → main → state=COMPLETED
              REJECTED → leaves findings, returns to step 4
```

---

## HANDOFF.md format

Both agents append to this file. Newest entry on top. Format:

```markdown
## [TIMESTAMP] [ROLE] [STATUS]

Body (markdown). Include:
- What you just did
- What you need from the other side
- Any blockers
- Test/coverage output if applicable
```

**Status tags Codex may emit:**
- `CONTRACT_DRAFT_READY` — contract written, awaiting auditor review
- `IMPLEMENTING` — working on code
- `BLOCKED` — needs decision/clarification
- `READY_FOR_AUDIT` — code + tests done, audit me
- `SPEC_REVISION_REQUEST` — believe the spec is wrong; do not edit, just flag

**Status tags Auditor may emit:**
- `SPEC_READY` — phase spec published; Codex may begin
- `CONTRACT_LOCKED` — contract approved, implementation may proceed
- `CONTRACT_REJECTED` — contract has issues; revise before coding
- `AUDIT_APPROVED` — phase complete, merging
- `AUDIT_REJECTED` — findings posted, fix and re-submit

---

## Branching

- `main` — stable, only Auditor merges here
- `feature/phase-N` — Codex's working branch for phase N
- `audit/phase-N` — Auditor's branch if SPEC/AUDIT changes need to be staged separately (rare; usually direct to main is fine)

**Codex never force-pushes. Auditor never force-pushes.**

---

## Conflict Resolution

If Codex disagrees with audit findings:
1. Leave `AUDIT_DISPUTE` entry in HANDOFF.md with rationale.
2. Do NOT edit AUDIT.yaml.
3. Wait for Auditor or human to respond.

If Auditor finds the spec was wrong mid-implementation:
1. Stop Codex via HANDOFF.md (`SPEC_REVISION_INCOMING`).
2. Update SPEC, bump version, commit.
3. Codex re-reads, may need to amend CONTRACT.

---

## Human Override

Oscar can override at any time. His commits supersede both agents. If he edits an artifact, both agents read the new version and continue from there.
