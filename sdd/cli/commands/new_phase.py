"""CLI command: sdd new-phase"""

import yaml
import typer
from datetime import datetime, UTC
from pathlib import Path

from sdd.state_machine.machine import StateMachine

app = typer.Typer()


@app.command("new-phase")
def new_phase(
    role: str = typer.Option(..., "--role", "-r", help="Role performing transition (must be auditor)"),
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
        with open(tmp, "w") as f:
            yaml.dump(contract_template, f, default_flow_style=False, sort_keys=False)
        import os
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
