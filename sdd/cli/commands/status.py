"""CLI command: sdd status"""

import json
import typer
from sdd.state_machine.machine import StateMachine

app = typer.Typer()


@app.command()
def status(json_output: bool = typer.Option(False, "--json", help="Output as JSON")):
    """Show current phase and state."""
    try:
        machine = StateMachine()
        state = machine.get_state()

        if json_output:
            typer.echo(json.dumps(state, indent=2))
        else:
            typer.echo(f"Phase: {state['current_phase']}")
            typer.echo(f"State: {state['current_state']}")
            typer.echo(f"Last Updated: {state['last_updated']}")
            typer.echo(f"Completed Phases: {state['completed_phases']}")
            if state["locked_at"]:
                typer.echo(f"Locked At: {state['locked_at']}")

    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
