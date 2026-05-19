"""SDD+ CLI entrypoint."""

import typer
from sdd.cli.commands.status import status
from sdd.cli.commands.validate import validate
from sdd.cli.commands.transition import transition
from sdd.cli.commands.init import init

app = typer.Typer()

# Register commands
app.command()(status)
app.command()(validate)
app.command()(transition)
app.command()(init)


if __name__ == "__main__":
    app()
