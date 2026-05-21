"""sdd metrics show -- display local SDD+ telemetry records."""

from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

import typer

from sdd.telemetry import query_audits, query_transitions

app = typer.Typer()


@app.command("show")
def show(
    phase: Optional[int] = typer.Option(
        None,
        "--phase",
        "-p",
        help="Filter records to a specific phase number.",
    ),
    since: Optional[str] = typer.Option(
        None,
        "--since",
        help="Filter records after this ISO-8601 datetime (e.g. 2026-05-20T00:00:00Z).",
    ),
    metrics_root: str = typer.Option(
        "",
        "--metrics-root",
        help="Override the .sdd-metrics directory path.",
    ),
) -> None:
    """Show local telemetry records (transitions and audits).

    Examples:
      sdd metrics show
      sdd metrics show --phase 4
      sdd metrics show --since 2026-05-20T00:00:00Z
    """
    root = Path(metrics_root) if metrics_root else None

    # Parse --since
    since_dt: Optional[datetime] = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            if since_dt.tzinfo is None:
                since_dt = since_dt.replace(tzinfo=UTC)
        except ValueError:
            typer.echo(f"FAIL: invalid --since value: {since!r} (expected ISO-8601)", err=True)
            raise typer.Exit(code=1)

    transitions = query_transitions(phase=phase, since=since_dt, metrics_root=root)
    audits = query_audits(phase=phase, since=since_dt, metrics_root=root)

    if not transitions and not audits:
        typer.echo("INFO: No metrics records found.")
        return

    if transitions:
        typer.echo(f"-- Transitions ({len(transitions)}) --")
        for r in transitions:
            typer.echo(
                f"  [{r.get('timestamp', '')[:19]}] "
                f"phase={r.get('phase')} "
                f"role={r.get('role')} "
                f"{r.get('from_state')} -> {r.get('to_state')}"
            )

    if audits:
        typer.echo(f"-- Audits ({len(audits)}) --")
        for r in audits:
            typer.echo(
                f"  [{r.get('timestamp', '')[:19]}] "
                f"phase={r.get('phase')} "
                f"verdict={r.get('verdict')} "
                f"coverage={r.get('coverage_pct')}% "
                f"findings={r.get('finding_count')}"
            )
