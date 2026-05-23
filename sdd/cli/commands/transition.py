"""CLI command: sdd transition"""

import json
import subprocess
import yaml
import typer
from pathlib import Path

from sdd.state_machine.machine import StateMachine
from sdd.state_machine.transitions import TransitionError

app = typer.Typer()

# Color palette for SDD state labels
_STATE_COLORS = {
    "DRAFT":         "e4e669",
    "REFINED":       "0075ca",
    "LOCKED":        "d93f0b",
    "IMPLEMENTING":  "0e8a16",
    "AUDITING":      "e11d48",
    "COMPLETED":     "6f42c1",
}

_ALL_SDD_STATES = set(_STATE_COLORS.keys())


# ---------------------------------------------------------------------------
# GitHub helpers (fail-open, never propagate to caller)
# ---------------------------------------------------------------------------


def _load_github_config() -> dict | None:
    """Read github_integration block from AGENTS.yaml. Returns None if absent/disabled."""
    agents_path = Path("AGENTS.yaml")
    if not agents_path.exists():
        return None
    try:
        with open(agents_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        cfg = data.get("github_integration", {})
        if not cfg.get("enabled", False):
            return None
        if not cfg.get("repo"):
            typer.echo("WARN: github_integration.repo is required but missing; skipping GitHub labels.")
            return None
        return cfg
    except Exception:
        return None


def _ensure_state_label(repo: str, state: str) -> bool:
    """Create the sdd:{state} label if it doesn't exist. Returns True on success."""
    label_name = f"sdd:{state}"
    color = _STATE_COLORS.get(state, "ededed")
    result = subprocess.run(
        ["gh", "label", "create", label_name,
         "--repo", repo,
         "--color", color,
         "--description", f"SDD phase state: {state}",
         "--force"],          # --force = update if already exists
        capture_output=True, text=True,
    )
    return result.returncode == 0


def _get_open_issues(repo: str, milestone_title: str | None) -> list[int]:
    """Return issue numbers to label. Prefers milestone issues; falls back to sdd:* labelled ones."""
    # Try milestone first
    if milestone_title:
        result = subprocess.run(
            ["gh", "issue", "list",
             "--repo", repo,
             "--milestone", milestone_title,
             "--state", "open",
             "--json", "number"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            try:
                issues = json.loads(result.stdout or "[]")
                numbers = [i["number"] for i in issues]
                if numbers:
                    return numbers
            except Exception:
                pass

    # Fallback: issues that already carry any sdd: label
    result = subprocess.run(
        ["gh", "issue", "list",
         "--repo", repo,
         "--state", "open",
         "--label", "sdd:DRAFT,sdd:REFINED,sdd:LOCKED,sdd:IMPLEMENTING,sdd:AUDITING,sdd:COMPLETED",
         "--json", "number"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        try:
            issues = json.loads(result.stdout or "[]")
            return [i["number"] for i in issues]
        except Exception:
            pass
    return []


def _remove_stale_state_labels(repo: str, issue_number: int) -> None:
    """Strip any sdd:* labels from the issue (fail-open)."""
    for state in _ALL_SDD_STATES:
        subprocess.run(
            ["gh", "issue", "edit", str(issue_number),
             "--repo", repo,
             "--remove-label", f"sdd:{state}"],
            capture_output=True, text=True,
        )


def _label_github_issues(phase: int, to_state: str, cfg: dict) -> None:
    """Fail-open: ensure label exists, find issues, swap state labels."""
    try:
        repo = cfg["repo"]
        milestone_title = f"Phase {phase}"

        # 1. Ensure the target label exists
        if not _ensure_state_label(repo, to_state):
            typer.echo(f"  WARN: could not create label sdd:{to_state}; skipping issue labelling.")
            return

        # 2. Find issues to update
        issue_numbers = _get_open_issues(repo, milestone_title)
        if not issue_numbers:
            typer.echo(f"  github labels: no open issues found for milestone '{milestone_title}'")
            return

        # 3. Swap labels on each issue
        labelled = 0
        for number in issue_numbers:
            _remove_stale_state_labels(repo, number)
            result = subprocess.run(
                ["gh", "issue", "edit", str(number),
                 "--repo", repo,
                 "--add-label", f"sdd:{to_state}"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                labelled += 1
            else:
                typer.echo(f"  WARN: could not label issue #{number}: {result.stderr.strip()}")

        typer.echo(f"  github labels: sdd:{to_state} applied to {labelled}/{len(issue_numbers)} issues")

    except Exception as exc:
        typer.echo(f"  WARN: GitHub label error: {exc}")


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


@app.command()
def transition(
    to_state: str = typer.Argument(..., help="Target state (DRAFT, REFINED, LOCKED, IMPLEMENTING, AUDITING, COMPLETED)"),
    role: str = typer.Option(..., "--role", "-r", help="Role performing transition (implementer or auditor)"),
    executor: str = typer.Option("any", "--executor", "-e", help="Executor for this action (e.g. claude, gpt-4, llama, human)"),
    github: bool = typer.Option(
        False,
        "--github",
        help="After transition, apply sdd:{STATE} label to open GitHub issues in the current phase milestone.",
    ),
):
    """Transition to a new state."""
    try:
        machine = StateMachine()
        result = machine.transition(to_state, role)

        typer.echo(f"OK: Transition successful: {result['from_state']} -> {result['to_state']}")
        typer.echo(f"  Timestamp: {result['timestamp']}")

        # Emit telemetry (fail-open -- never raises)
        try:
            from sdd.telemetry import emit_transition
            current_phase = machine.get_state().get("current_phase", 0)
            emit_transition(
                phase=current_phase,
                role=role,
                from_state=result["from_state"],
                to_state=result["to_state"],
                executor=executor,
            )
        except Exception:
            pass

        # GitHub label sync (fail-open)
        if github:
            gh_cfg = _load_github_config()
            if gh_cfg:
                try:
                    phase = machine.get_state().get("current_phase", 0)
                except Exception:
                    phase = 0
                _label_github_issues(phase, result["to_state"], gh_cfg)

    except TransitionError as e:
        typer.echo(f"FAIL: Transition denied: {e}", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"FAIL: Error: {e}", err=True)
        raise typer.Exit(1)
    except FileNotFoundError as e:
        typer.echo(f"FAIL: Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"FAIL: Unexpected error: {e}", err=True)
        raise typer.Exit(1)
