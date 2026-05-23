"""CLI command: sdd validate"""

from typing import Callable, Optional

import typer
from pathlib import Path

from sdd.validators.validate_contract import validate_contract
from sdd.validators.validate_state import validate_state

app = typer.Typer()


# Registry of available validators -- adding a new schema is one line here.
_VALIDATORS: dict[str, Callable] = {
    "contract": validate_contract,
    "state": validate_state,
}


def _detect_schema(artifact_path: str) -> Optional[str]:
    """Infer the schema name from the file path. Returns None if ambiguous."""
    lowered = artifact_path.lower()
    if "contract" in lowered:
        return "contract"
    if "state" in lowered:
        return "state"
    return None


@app.command()
def validate(
    artifact_path: str = typer.Argument(..., help="Path to YAML artifact to validate"),
    schema: str = typer.Option(None, "--schema", "-s", help="Schema to validate against (contract, state)"),
):
    """Validate a YAML artifact."""
    if not Path(artifact_path).exists():
        typer.echo(f"Error: File not found: {artifact_path}", err=True)
        raise typer.Exit(1)

    if schema is None:
        schema = _detect_schema(artifact_path)
        if schema is None:
            typer.echo(
                "Error: Cannot auto-detect schema. Use --schema to specify (contract or state)",
                err=True,
            )
            raise typer.Exit(1)

    validator = _VALIDATORS.get(schema)
    if validator is None:
        typer.echo(f"Error: Unknown schema: {schema}", err=True)
        raise typer.Exit(1)

    result = validator(artifact_path)

    if result.valid:
        typer.echo(f"OK: {artifact_path} is valid ({result.schema_name})")
        raise typer.Exit(0)
    typer.echo(f"FAIL: {artifact_path} is invalid ({result.schema_name})", err=True)
    for error in result.errors:
        typer.echo(f"  - {error.field}: {error.message}", err=True)
    raise typer.Exit(1)
