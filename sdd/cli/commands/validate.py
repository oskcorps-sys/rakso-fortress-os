"""CLI command: sdd validate"""

import typer
from pathlib import Path
from sdd.validators.validate_contract import validate_contract
from sdd.validators.validate_state import validate_state

app = typer.Typer()


@app.command()
def validate(
    artifact_path: str = typer.Argument(..., help="Path to YAML artifact to validate"),
    schema: str = typer.Option(None, "--schema", "-s", help="Schema to validate against (contract, state)"),
):
    """Validate a YAML artifact."""
    path = Path(artifact_path)

    if not path.exists():
        typer.echo(f"Error: File not found: {artifact_path}", err=True)
        raise typer.Exit(1)

    # Auto-detect schema if not provided
    if schema is None:
        if "contract" in artifact_path.lower() or "CONTRACT" in artifact_path:
            schema = "contract"
        elif "state" in artifact_path.lower() or "STATE" in artifact_path:
            schema = "state"
        else:
            typer.echo("Error: Cannot auto-detect schema. Use --schema to specify (contract or state)", err=True)
            raise typer.Exit(1)

    # Validate
    if schema == "contract":
        result = validate_contract(artifact_path)
    elif schema == "state":
        result = validate_state(artifact_path)
    else:
        typer.echo(f"Error: Unknown schema: {schema}", err=True)
        raise typer.Exit(1)

    # Output
    if result.valid:
        typer.echo(f"OK: {artifact_path} is valid ({result.schema})")
        raise typer.Exit(0)
    else:
        typer.echo(f"FAIL: {artifact_path} is invalid ({result.schema})", err=True)
        for error in result.errors:
            typer.echo(f"  - {error.field}: {error.message}", err=True)
        raise typer.Exit(1)
