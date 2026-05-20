"""CLI command: sdd transition"""

import typer
from sdd.state_machine.machine import StateMachine
from sdd.state_machine.transitions import TransitionError

app = typer.Typer()


@app.command()
def transition(
    to_state: str = typer.Argument(..., help="Target state (DRAFT, REFINED, LOCKED, IMPLEMENTING, AUDITING, COMPLETED)"),
    role: str = typer.Option(..., "--role", "-r", help="Role performing transition (implementer or auditor)"),
):
    """Transition to a new state."""
    try:
        machine = StateMachine()
        result = machine.transition(to_state, role)

        typer.echo(f"OK: Transition successful: {result['from_state']} -> {result['to_state']}")
        typer.echo(f"  Timestamp: {result['timestamp']}")

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
