# Third-Party Audit Prompt

Copy this prompt into a DIFFERENT AI (Gemini, GPT-4, Codex, etc.) along with the repo files.
The auditor must NOT be the same AI that built the project.

---

## Prompt

You are an independent code auditor. You did NOT build this project. You have no prior context.

**Project**: SDD+ (Specification-Driven Development Extended)
**Language**: Python 3.13+
**Framework**: CLI (Typer) + FastAPI web dashboard
**Size**: ~2,075 lines of code, 261 tests, 92% coverage

### Audit scope

Review the codebase for:

1. **Architecture & Design**
   - Is the module structure clean and well-separated?
   - Are there circular dependencies?
   - Is the state machine implementation correct and complete?
   - Are the Pydantic schemas well-designed?

2. **Security**
   - Are there injection risks in subprocess calls?
   - Is user input properly validated?
   - Are file operations safe (path traversal, symlink attacks)?
   - Is YAML loading safe (yaml.safe_load vs yaml.load)?
   - Are there secrets or credentials accidentally committed?

3. **Test Quality**
   - Do tests actually test meaningful behavior, or are they trivial?
   - Are edge cases covered?
   - Is mocking appropriate, or does it hide real bugs?
   - Are there tests that would pass even if the code was broken?

4. **Spec Conformance**
   - Do the CONTRACT.yaml files match what the code actually does?
   - Do the SPEC.yaml files match the implementation?
   - Is the AGENTS.yaml authority matrix actually enforced?

5. **Documentation Accuracy**
   - Does the README match the actual CLI commands?
   - Are the install instructions correct?
   - Is the architecture diagram accurate?

6. **Packaging**
   - Is pyproject.toml correctly configured?
   - Will `pip install sdd-plus` work?
   - Are dependencies pinned appropriately?

7. **Code Quality**
   - Dead code?
   - Duplicated logic?
   - Overly complex functions?
   - Error handling: is fail-open (try/except pass) appropriate everywhere it's used?

### Output format

Produce a structured audit report:

```
## Audit Report: SDD+ v0.2.0

### Executive Summary
[1 paragraph: overall assessment]

### Findings

#### CRITICAL (must fix before release)
- [Finding] — [File:Line] — [Description]

#### HIGH (should fix)
- [Finding] — [File:Line] — [Description]

#### MEDIUM (recommended)
- [Finding] — [File:Line] — [Description]

#### LOW (informational)
- [Finding] — [File:Line] — [Description]

### Strengths
- [What's done well]

### Verdict
[APPROVED / APPROVED WITH CONDITIONS / REJECTED]
```

### Files to provide

Give the auditor these files (in order of importance):
1. `sdd/` — all Python source files
2. `tests/` — all test files
3. `AGENTS.yaml` — authority matrix
4. `pyproject.toml` — packaging config
5. `sdd/artifacts/` — specs, contracts, audits
6. `README.md`
7. `CHANGELOG.md`
