"""sdd check-patterns — report file-pattern violations for a role + fileset.

Used as a dry-run tool and called by the SDD pre-commit hook.
"""

from pathlib import Path
from typing import Optional

import typer

from sdd.enforcement import (
    check_files,
    get_forbidden_patterns,
    get_staged_files,
    load_agents_config,
    resolve_role,
)

app = typer.Typer()


@app.command("check-patterns")
def check_patterns(
    role: Optional[str] = typer.Option(
        None,
        "--role",
        "-r",
        help="Role to check against.  Defaults to resolved role (SDD_ROLE env / .sdd-role file).",
    ),
    files: Optional[list[str]] = typer.Option(
        None,
        "--files",
        "-f",
        help="Explicit list of files to check (repeatable).  Mutually exclusive with --staged.",
    ),
    staged: bool = typer.Option(
        False,
        "--staged",
        help="Check git-staged files (used by the pre-commit hook).",
    ),
    repo_root: str = typer.Option(
        "",
        "--repo-root",
        help="Path to the git repository root (default: current directory).",
    ),
) -> None:
    """Check file paths against the active role's forbidden_file_patterns.

    Exit 0 when there are no violations or when no role is active (advisory
    no-op).  Exit 1 when one or more violations are found.

    Examples:
      sdd check-patterns --role implementer --files sdd/artifacts/PHASE_4_SPEC.yaml
      sdd check-patterns --staged                 # called by the pre-commit hook
    """
    root = Path(repo_root) if repo_root else None

    # --- resolve role ---
    active_role = role or resolve_role(root)
    if not active_role:
        typer.echo("INFO: No role set - enforcement is a no-op (advisory mode).")
        raise typer.Exit(code=0)

    # --- resolve fileset ---
    if staged:
        target_files = get_staged_files(root)
    elif files:
        target_files = list(files)
    else:
        typer.echo("INFO: No files specified and --staged not set.  Nothing to check.")
        raise typer.Exit(code=0)

    if not target_files:
        typer.echo("OK: No files to check.")
        raise typer.Exit(code=0)

    # --- load patterns ---
    config = load_agents_config(root)
    if config is None:
        typer.echo("INFO: AGENTS.yaml not found - enforcement disabled (no-op).")
        raise typer.Exit(code=0)

    forbidden = get_forbidden_patterns(active_role, config)
    if not forbidden:
        typer.echo(f"OK: No forbidden patterns defined for role '{active_role}'.")
        raise typer.Exit(code=0)

    # --- check ---
    violations = check_files(target_files, active_role, forbidden)

    if not violations:
        typer.echo(f"OK: No violations for role '{active_role}'.")
        raise typer.Exit(code=0)

    typer.echo(
        f"FAIL: {len(violations)} violation(s) for role '{active_role}':", err=True
    )
    for v in violations:
        typer.echo(f"  file   : {v['file']}", err=True)
        typer.echo(f"  rule   : {v['pattern']}", err=True)
        typer.echo("", err=True)
    raise typer.Exit(code=1)
