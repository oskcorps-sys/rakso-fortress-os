"""sdd dashboard -- launch the SDD+ web dashboard."""

from pathlib import Path

import typer

app = typer.Typer()


@app.command("dashboard")
def dashboard(
    port: int = typer.Option(8888, "--port", "-p", help="Port to serve on."),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to."),
    project_root: str = typer.Option(
        "",
        "--project-root",
        help="SDD+ project root directory (default: current directory).",
    ),
) -> None:
    """Launch the SDD+ web dashboard (read-only).

    Opens a local HTTP server at http://HOST:PORT with project status,
    audit history, and telemetry metrics.
    """
    root = Path(project_root) if project_root else None

    from sdd.web.app import create_app

    web_app = create_app(project_root=root)

    typer.echo(f"SDD+ Dashboard starting at http://{host}:{port}")
    typer.echo("Press Ctrl+C to stop.")

    import uvicorn

    uvicorn.run(web_app, host=host, port=port, log_level="warning")
