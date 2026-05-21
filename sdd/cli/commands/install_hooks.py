"""sdd install-hooks — install the SDD pre-commit hook for a given role."""

from pathlib import Path

import typer

from sdd.enforcement import install_hook

app = typer.Typer()


@app.command("install-hooks")
def install_hooks(
    role: str = typer.Option(
        ...,
        "--role",
        "-r",
        help="Role to record in .sdd-role (implementer or auditor).",
    ),
    repo_root: str = typer.Option(
        "",
        "--repo-root",
        help="Path to the git repository root (default: current directory).",
    ),
) -> None:
    """Install the SDD+ pre-commit hook and record the active role.

    If a pre-existing non-SDD hook is found it is backed up to
    .git/hooks/pre-commit.pre-sdd before the SDD hook is written.

    The hook calls `sdd check-patterns --staged` on every commit.
    """
    root = Path(repo_root) if repo_root else None
    result = install_hook(role=role, repo_root=root)

    if not result["installed"]:
        typer.echo(f"FAIL: {result['message']}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"OK: {result['message']}")
    typer.echo(f"  hook  -> {result['hook_path']}")
    typer.echo(f"  role  -> {result['role_file']} ({role})")
    if result["backed_up"]:
        typer.echo("  backup -> pre-commit.pre-sdd")
