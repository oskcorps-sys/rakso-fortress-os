"""CLI command group: sdd projects"""

import typer

from sdd.workspace import add_project, remove_project, list_projects

app = typer.Typer(help="Manage multi-project workspace")


@app.command("list")
def projects_list():
    """List all projects in the workspace."""
    projects = list_projects()
    if not projects:
        typer.echo("No projects registered. Use `sdd projects add` to add one.")
        return

    typer.echo(f"{'Name':<20} {'Phase':<8} {'State':<16} Path")
    typer.echo("-" * 70)
    for p in projects:
        typer.echo(f"{p['name']:<20} {str(p['phase']):<8} {p['state']:<16} {p['path']}")


@app.command("add")
def projects_add(
    path: str = typer.Argument(..., help="Path to the SDD project directory"),
    name: str = typer.Option(None, "--name", "-n", help="Project name (defaults to directory name)"),
):
    """Add a project to the workspace."""
    from pathlib import Path as P

    project_name = name or P(path).resolve().name
    try:
        add_project(project_name, path)
        typer.echo(f"Added '{project_name}' ({P(path).resolve()})")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("remove")
def projects_remove(
    path: str = typer.Argument(..., help="Path to the project to remove"),
):
    """Remove a project from the workspace."""
    try:
        remove_project(path)
        typer.echo(f"Removed project at {path}")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
