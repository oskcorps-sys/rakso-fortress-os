"""CLI command: sdd audit"""

import json
import os
import subprocess
import sys
import yaml
import typer
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from sdd.state_machine.machine import StateMachine

app = typer.Typer()


@app.command()
def audit(
    role: str = typer.Option(..., "--role", "-r", help="Role performing audit (must be auditor)"),
    phase: Optional[int] = typer.Option(None, "--phase", "-p", help="Phase to audit (default: current)"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip manual review"),
    git: bool = typer.Option(
        False,
        "--git",
        help="After an APPROVED verdict, stage and commit the AUDIT.yaml artifact.",
    ),
):
    """Run the 4-step audit loop and produce AUDIT.yaml."""
    if role != "auditor":
        typer.echo("Error: Only auditor role can run audits", err=True)
        raise typer.Exit(1)

    try:
        machine = StateMachine()
        state = machine.get_state()
        audit_phase = phase or state["current_phase"]
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    findings = []
    steps = {}

    # Step 1: Run pytest
    cov_json = "coverage.json"
    cmd = [
        sys.executable, "-m", "pytest", "tests/", "-v",
        "--cov=sdd", f"--cov-report=json:{cov_json}",
        "--tb=short", "--no-header", "-q",
    ]
    test_result = subprocess.run(cmd, capture_output=True, text=True)
    tests_pass = test_result.returncode == 0
    steps["pytest"] = {"passed": tests_pass, "returncode": test_result.returncode}

    if not tests_pass:
        findings.append({"severity": "HIGH", "description": "Test failures detected"})

    # Step 2: Check coverage
    coverage_pct = 0.0
    if Path(cov_json).exists():
        try:
            with open(cov_json, "r", encoding="utf-8") as f:
                cov_data = json.load(f)
            coverage_pct = cov_data.get("totals", {}).get("percent_covered", 0.0)
        except Exception:
            pass
        finally:
            try:
                os.remove(cov_json)
            except OSError:
                pass

    coverage_pass = coverage_pct >= 85.0
    steps["coverage"] = {"percent": round(coverage_pct, 1), "threshold": 85.0, "passed": coverage_pass}

    if not coverage_pass:
        findings.append({
            "severity": "HIGH",
            "description": f"Coverage {coverage_pct:.1f}% below 85% threshold",
        })

    # Step 3: Spec conformance — check deliverable files exist
    spec_path = f"sdd/artifacts/PHASE_{audit_phase}_SPEC.yaml"
    spec_pass = True
    missing_files = []

    if Path(spec_path).exists():
        try:
            with open(spec_path, "r", encoding="utf-8") as f:
                spec_data = yaml.safe_load(f)
            included = []
            scope = spec_data.get("scope", {})
            if isinstance(scope, dict):
                included = scope.get("included", [])
            for item in included:
                file_path = item.split(" — ")[0].strip() if " — " in item else item.strip()
                if file_path and not Path(file_path).exists():
                    missing_files.append(file_path)
        except Exception:
            pass

    if missing_files:
        spec_pass = False
        findings.append({
            "severity": "MEDIUM",
            "description": f"Missing spec deliverables: {', '.join(missing_files[:5])}",
        })

    steps["spec_conformance"] = {"passed": spec_pass, "missing_files": missing_files}

    # Step 4: Contract conformance — check acceptance tests exist
    contract_path = f"sdd/artifacts/PHASE_{audit_phase}_CONTRACT.yaml"
    contract_pass = True
    missing_tests = []

    if Path(contract_path).exists():
        try:
            with open(contract_path, "r", encoding="utf-8") as f:
                contract_data = yaml.safe_load(f)
            acceptance_tests = contract_data.get("acceptance_tests", [])
            test_names = set()
            for test_file in Path("tests").glob("test_*.py"):
                content = test_file.read_text(encoding="utf-8", errors="ignore")
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("def test_"):
                        name = stripped.split("(")[0].replace("def ", "")
                        test_names.add(name)

            for at in acceptance_tests:
                if not isinstance(at, dict):
                    continue
                # Skip criteria verified by other audit steps (coverage, conformance, etc.)
                if at.get("kind") == "criterion":
                    continue
                name = at.get("name", "")
                if name and name not in test_names:
                    missing_tests.append(name)
        except Exception:
            pass

    if missing_tests:
        contract_pass = False
        findings.append({
            "severity": "MEDIUM",
            "description": f"Missing acceptance tests: {', '.join(missing_tests[:5])}",
        })

    steps["contract_conformance"] = {"passed": contract_pass, "missing_tests": missing_tests}

    # Build verdict
    verdict = "APPROVED" if (tests_pass and coverage_pass) else "REJECTED"

    audit_data = {
        "audit_id": f"audit-phase-{audit_phase}-v1",
        "phase": audit_phase,
        "timestamp": datetime.now(UTC).isoformat(),
        "auditor": role,
        "verdict": verdict,
        "steps": steps,
        "findings": findings,
        "coverage_percent": round(coverage_pct, 1),
    }

    if auto_approve and verdict == "APPROVED":
        audit_data["signed_at"] = datetime.now(UTC).isoformat()

    # Write AUDIT.yaml
    audit_file = f"sdd/artifacts/PHASE_{audit_phase}_AUDIT.yaml"
    Path(audit_file).parent.mkdir(parents=True, exist_ok=True)
    tmp_file = f"{audit_file}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        yaml.dump(audit_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    os.replace(tmp_file, audit_file)

    # Emit telemetry (fail-open -- never raises)
    try:
        from sdd.telemetry import emit_audit
        emit_audit(
            phase=audit_phase,
            verdict=verdict,
            coverage_pct=coverage_pct,
            finding_count=len(findings),
        )
    except Exception:
        pass

    # Output
    if verdict == "APPROVED":
        typer.echo(f"APPROVED Phase {audit_phase} - {coverage_pct:.1f}% coverage, all tests pass")
        if git:
            from sdd.git_integration import is_git_repo, stage_and_commit
            repo_root = Path.cwd()
            if not is_git_repo(repo_root):
                typer.echo("WARN: --git specified but not in a git repository; skipping commit.")
            else:
                commit_msg = (
                    f"audit(phase-{audit_phase}): APPROVED {coverage_pct:.1f}% coverage"
                )
                git_result = stage_and_commit(commit_msg, [audit_file], repo_root)
                if git_result["success"]:
                    typer.echo(f"  git commit: {git_result['sha']} {commit_msg}")
                else:
                    typer.echo(f"  WARN: git commit failed: {git_result['message']}")
    else:
        typer.echo(f"REJECTED Phase {audit_phase}", err=True)
        for finding in findings:
            typer.echo(f"  - [{finding['severity']}] {finding['description']}", err=True)
        raise typer.Exit(1)
