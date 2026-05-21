"""
sdd/telemetry.py -- Local JSONL telemetry for SDD+ lifecycle events.

Two event types are emitted:

  sdd.phase.transition
    phase, role, from_state, to_state, timestamp

  sdd.audit.result
    phase, verdict, coverage_pct, test_count, finding_count, timestamp

Records are appended as newline-delimited JSON to:
  .sdd-metrics/transitions.jsonl
  .sdd-metrics/audits.jsonl

The store is created lazily.  Any I/O error is silently suppressed so
that telemetry never breaks a lifecycle command (fail-open).

No new top-level dependencies: stdlib json, pathlib, datetime only.

The metrics root can be overridden via the SDD_METRICS_ROOT environment
variable, which is useful in tests.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_METRICS_DIR = ".sdd-metrics"
TRANSITIONS_FILE = "transitions.jsonl"
AUDITS_FILE = "audits.jsonl"


# ---------------------------------------------------------------------------
# Store helpers
# ---------------------------------------------------------------------------


def _metrics_root(override: Path | None = None) -> Path:
    """Return the metrics directory path.

    Resolution order:
      1. *override* argument (used in tests)
      2. SDD_METRICS_ROOT environment variable
      3. DEFAULT_METRICS_DIR relative to cwd
    """
    if override is not None:
        return override
    env = os.environ.get("SDD_METRICS_ROOT", "").strip()
    if env:
        return Path(env)
    return Path(DEFAULT_METRICS_DIR)


def _append_record(root: Path, filename: str, record: dict) -> None:
    """Append *record* as a JSON line to *root/filename*.

    Silently drops the record on any I/O error (fail-open).
    """
    try:
        root.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=True) + "\n"
        with open(root / filename, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        pass  # fail-open -- never propagate telemetry errors


def _read_records(root: Path, filename: str) -> list[dict]:
    """Read all JSON records from *root/filename*.

    Returns an empty list if the file does not exist or cannot be read.
    """
    path = root / filename
    if not path.exists():
        return []
    records: list[dict] = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass  # skip malformed lines
    except Exception:
        pass
    return records


# ---------------------------------------------------------------------------
# Emit functions
# ---------------------------------------------------------------------------


def emit_transition(
    phase: int,
    role: str,
    from_state: str,
    to_state: str,
    metrics_root: Path | None = None,
) -> None:
    """Append a sdd.phase.transition event to transitions.jsonl."""
    record = {
        "event": "sdd.phase.transition",
        "timestamp": datetime.now(UTC).isoformat(),
        "phase": phase,
        "role": role,
        "from_state": from_state,
        "to_state": to_state,
    }
    _append_record(_metrics_root(metrics_root), TRANSITIONS_FILE, record)


def emit_audit(
    phase: int,
    verdict: str,
    coverage_pct: float,
    finding_count: int,
    test_count: Optional[int] = None,
    metrics_root: Path | None = None,
) -> None:
    """Append a sdd.audit.result event to audits.jsonl."""
    record = {
        "event": "sdd.audit.result",
        "timestamp": datetime.now(UTC).isoformat(),
        "phase": phase,
        "verdict": verdict,
        "coverage_pct": round(coverage_pct, 1),
        "test_count": test_count,
        "finding_count": finding_count,
    }
    _append_record(_metrics_root(metrics_root), AUDITS_FILE, record)


# ---------------------------------------------------------------------------
# Query functions
# ---------------------------------------------------------------------------


def _parse_ts(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp string into a timezone-aware datetime."""
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def query_transitions(
    phase: Optional[int] = None,
    since: Optional[datetime] = None,
    metrics_root: Path | None = None,
) -> list[dict]:
    """Return transition records, optionally filtered by phase and/or timestamp."""
    records = _read_records(_metrics_root(metrics_root), TRANSITIONS_FILE)
    if phase is not None:
        records = [r for r in records if r.get("phase") == phase]
    if since is not None:
        # Ensure since is timezone-aware
        if since.tzinfo is None:
            since = since.replace(tzinfo=UTC)
        records = [r for r in records if _parse_ts(r.get("timestamp", "1970-01-01T00:00:00Z")) >= since]
    return records


def query_audits(
    phase: Optional[int] = None,
    since: Optional[datetime] = None,
    metrics_root: Path | None = None,
) -> list[dict]:
    """Return audit records, optionally filtered by phase and/or timestamp."""
    records = _read_records(_metrics_root(metrics_root), AUDITS_FILE)
    if phase is not None:
        records = [r for r in records if r.get("phase") == phase]
    if since is not None:
        if since.tzinfo is None:
            since = since.replace(tzinfo=UTC)
        records = [r for r in records if _parse_ts(r.get("timestamp", "1970-01-01T00:00:00Z")) >= since]
    return records
