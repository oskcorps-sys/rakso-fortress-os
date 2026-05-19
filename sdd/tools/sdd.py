"""
SDD+ CLI - Main entry point for sdd commands.

Usage:
    sdd --help                           # Show all commands
    sdd validate contract                # Validate CONTRACT.yaml
    sdd snapshot                         # Show current state
    
(More commands added in Phase 2+)
"""

import typer
from typing import Optional
from pathlib import Path
import json
from datetime import datetime

app = typer.Typer(
    name="sdd",
    help="Specification-Driven Development Extended - CLI tool",
    no_args_is_help=True,
)


@app.command()
def validate(
    artifact: str = typer.Argument(..., help="Artifact to validate: contract, state"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Custom path to artifact"),
):
    """
    Validate artifacts against their schemas.
    
    Examples:
        sdd validate contract
        sdd validate state
        sdd validate contract --path ./my-contract.yaml
    """
    typer.echo(f"[Phase 2+] Validate {artifact} command", err=True)
    raise typer.Exit(code=1)


@app.command()
def snapshot():
    """
    Show current state snapshot.
    
    Displays: current phase, status, last transition, next phase.
    """
    typer.echo(f"[Phase 2+] Snapshot command", err=True)
    raise typer.Exit(code=1)


@app.command()
def log(
    phase: Optional[int] = typer.Option(None, "--phase", "-p", help="Filter by phase number"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Filter by agent: codex, claude-code"),
):
    """
    Show audit logs.
    
    Examples:
        sdd log                        # Show all logs
        sdd log --phase 1              # Show Phase 1 logs
        sdd log --agent codex          # Show Codex actions
    """
    typer.echo(f"[Phase 2+] Log command", err=True)
    raise typer.Exit(code=1)


@app.command()
def transition(
    from_state: str = typer.Option(..., "--from", help="Current state (e.g., DRAFT)"),
    to_state: str = typer.Option(..., "--to", help="Target state (e.g., REFINED)"),
):
    """
    Transition state (admin-only in Phase 2+).
    
    Validates transition against STATE_MACHINE.yaml.
    Updates STATE_SNAPSHOT.yaml and logs.
    
    Examples:
        sdd transition --from DRAFT --to REFINED
    """
    typer.echo(f"[Phase 2+] Transition command", err=True)
    raise typer.Exit(code=1)


@app.command()
def init():
    """
    Initialize a new SDD+ project.
    
    Creates:
        - /sdd directory structure
        - /tests directory
        - Initial YAML artifacts
    """
    typer.echo("✓ SDD+ project ready", err=False)
    typer.echo("  - Phase 0: Bootstrap complete", err=False)
    typer.echo("  - Read AGENTS.md (implementer) and CLAUDE.md (auditor)", err=False)
    typer.echo("  - Run: pytest tests/ -v --cov", err=False)


@app.callback()
def callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """SDD+ CLI - Specification-Driven Development Extended"""
    if verbose:
        typer.echo("[DEBUG] Verbose mode enabled")


if __name__ == "__main__":
    app()
