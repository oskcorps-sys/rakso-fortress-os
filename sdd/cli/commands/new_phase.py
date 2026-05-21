"""CLI command: sdd new-phase"""

import os
import yaml
import typer
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from sdd.state_machine.machine import StateMachine

app = typer.Typer()


@app.command("new-phase")
def new_phase(
    role: str = typer.Option(..., "--role", "-r", help="Role performing transition (must be auditor)"),
    git: bool = typer.Option(
        False,
        "--git",
        help="After advancing the phase create a feature/phase-N git branch.",
    ),
):
    """Advance to the next phase after current phase is COMPLETED."""
    if role != "auditor":
        typer.echo("Error: Only auditor role can advance phases", err=True)
        raise typer.Exit(1)

    try:
        machine = StateMachine()
        state = machine.get_state()
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if state["current_state"] != "COMPLETED":
        typer.echo(
            f"Error: Current phase must be COMPLETED to advance "
            f"(currently {state['current_state']})",
            err=True,
        )
        raise typer.Exit(1)

    current = state["current_phase"]
    next_phase = current + 1

    # Create template contract for new phase
    contract_path = f"sdd/artifacts/PHASE_{next_phase}_CONTRACT.yaml"
    if not Path(contract_path).exists():
        contract_template = {
            "phase": next_phase,
            "contract_id": f"contract-phase-{next_phase}-v1",
            "created_at": datetime.now(UTC).isoformat(),
            "status": "DRAFT",
            "specification": {
                "title": f"Phase {next_phase} — [TITLE]",
                "description": "TODO: describe this phase",
                "success_criteria": [],
            },
            "acceptance_tests": [],
            "files_to_create": [],
            "files_to_modify": [],
            "scope_is_locked": False,
        }
        Path(contract_path).parent.mkdir(parents=True, exist_ok=True)
        tmp = f"{contract_path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            yaml.dump(contract_template, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        os.replace(tmp, contract_path)

    # Create handoff log
    handoff_dir = Path("sdd/handoffs")
    handoff_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = handoff_dir / f"PHASE_{current}_TO_{next_phase}.md"
    if not handoff_path.exists():
        handoff_path.write_text(
            f"# Handoff: Phase {current} -> Phase {next_phase}\n\n"
            f"- Completed: {datetime.now(UTC).isoformat()}\n"
            f"- Completed phases: {state['completed_phases']}\n\n"
            f"## Summary\n\nTODO: summarize what was delivered in Phase {current}.\n\n"
            f"## Carry-forward\n\nTODO: note anything the next phase should be aware of.\n",
            encoding="utf-8",
        )

    result = machine.start_new_phase(next_phase)
    typer.echo(
        f"Phase {result['old_phase']} -> Phase {result['new_phase']} "
        f"(state reset to DRAFT)"
    )
    typer.echo(f"  Contract template: {contract_path}")
    typer.echo(f"  Handoff log: {handoff_path}")

    if git:
        from sdd.git_integration import create_branch, is_git_repo
        repo_root = Path.cwd()
        if not is_git_repo(repo_root):
            typer.echo("WARN: --git specified but not in a git repository; skipping branch creation.")
        else:
            branch_name = f"feature/phase-{next_phase}"
            git_result = create_branch(branch_name, repo_root)
            if git_result["success"]:
                typer.echo(f"  git branch: {branch_name} (created)")
            else:
                typer.echo(f"  WARN: git branch creation failed: {git_result['message']}")
