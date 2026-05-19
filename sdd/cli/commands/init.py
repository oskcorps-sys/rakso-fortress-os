"""CLI command: sdd init"""

import typer
from pathlib import Path
import yaml
from datetime import datetime, UTC

app = typer.Typer()


@app.command()
def init(
    project_name: str = typer.Argument(..., help="Name of new SDD project"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing project"),
):
    """Scaffold a new SDD project."""
    project_dir = Path(project_name)

    if project_dir.exists() and not force:
        typer.echo(f"Error: Directory already exists: {project_name}", err=True)
        typer.echo("Use --force to overwrite", err=True)
        raise typer.Exit(1)

    # Create directory
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create CONTRACT.yaml template
    contract_template = {
        "phase": 1,
        "contract_id": f"contract-{project_name}-v1",
        "created_at": datetime.now(UTC).isoformat(),
        "status": "DRAFT",
        "specification": {
            "title": f"{project_name} Phase 1",
            "description": "Add description here",
            "success_criteria": ["Criterion 1"],
        },
        "constraints": [],
        "assumptions": [],
        "acceptance_tests": [],
    }

    contract_path = project_dir / "CONTRACT.yaml"
    with open(contract_path, "w") as f:
        yaml.dump(contract_template, f, default_flow_style=False, sort_keys=False)

    # Create STATE_SNAPSHOT.yaml template
    state_template = {
        "phase": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "current_phase": 1,
        "current_state": "DRAFT",
        "completed_phases": [],
    }

    state_path = project_dir / "STATE_SNAPSHOT.yaml"
    with open(state_path, "w") as f:
        yaml.dump(state_template, f, default_flow_style=False, sort_keys=False)

    # Create .gitignore
    gitignore_content = """*.pyc
__pycache__/
.pytest_cache/
.coverage
htmlcov/
*.egg-info/
dist/
build/
.DS_Store
*.swp
*.swo
.venv/
venv/
"""

    gitignore_path = project_dir / ".gitignore"
    with open(gitignore_path, "w") as f:
        f.write(gitignore_content)

    typer.echo(f"✓ Project scaffolded: {project_name}/")
    typer.echo(f"  - CONTRACT.yaml")
    typer.echo(f"  - STATE_SNAPSHOT.yaml")
    typer.echo(f"  - .gitignore")
