"""SDD+ CLI entrypoint."""

import typer
from sdd.cli.commands.status import status
from sdd.cli.commands.validate import validate
from sdd.cli.commands.transition import transition
from sdd.cli.commands.init import init
from sdd.cli.commands.audit import audit
from sdd.cli.commands.new_phase import new_phase
from sdd.cli.commands.projects import app as projects_app

app = typer.Typer()

# Register commands
app.command()(status)
app.command()(validate)
app.command()(transition)
app.command()(init)
app.command()(audit)
app.command("new-phase")(new_phase)
app.add_typer(projects_app, name="projects")


if __name__ == "__main__":
    app()
