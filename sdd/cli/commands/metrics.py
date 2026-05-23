"""sdd metrics show -- display local SDD+ telemetry records."""

from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

import typer

from sdd.telemetry import query_audits, query_transitions

app = typer.Typer()


def _parse_since(since: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 datetime, defaulting tz-naive values to UTC.

    Raises typer.Exit(1) on parse failure (with a user-friendly message).
    """
    if since is None:
        return None
    try:
        dt = datetime.fromisoformat(since)
    except ValueError:
        typer.echo(f"FAIL: invalid --since value: {since!r} (expected ISO-8601)", err=True)
        raise typer.Exit(code=1)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _print_transitions(records: list[dict]) -> None:
    typer.echo(f"-- Transitions ({len(records)}) --")
    for r in records:
        typer.echo(
            f"  [{r.get('timestamp', '')[:19]}] "
            f"phase={r.get('phase')} "
            f"role={r.get('role')} "
            f"{r.get('from_state')} -> {r.get('to_state')}"
        )


def _print_audits(records: list[dict]) -> None:
    typer.echo(f"-- Audits ({len(records)}) --")
    for r in records:
        typer.echo(
            f"  [{r.get('timestamp', '')[:19]}] "
            f"phase={r.get('phase')} "
            f"verdict={r.get('verdict')} "
            f"coverage={r.get('coverage_pct')}% "
            f"findings={r.get('finding_count')}"
        )


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
    since_dt = _parse_since(since)

    transitions = query_transitions(phase=phase, since=since_dt, metrics_root=root)
    audits = query_audits(phase=phase, since=since_dt, metrics_root=root)

    if not transitions and not audits:
        typer.echo("INFO: No metrics records found.")
        return

    if transitions:
        _print_transitions(transitions)
    if audits:
        _print_audits(audits)
