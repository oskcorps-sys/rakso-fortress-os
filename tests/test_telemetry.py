"""Tests for sdd/telemetry.py -- local JSONL metrics store."""

import json
from datetime import datetime, UTC, timedelta
from pathlib import Path

import pytest

from sdd.telemetry import (
    emit_audit,
    emit_transition,
    query_audits,
    query_transitions,
)


# ---------------------------------------------------------------------------
# emit_transition
# ---------------------------------------------------------------------------


class TestEmitTransition:
    def test_creates_transitions_file(self, tmp_path):
        emit_transition(4, "auditor", "IMPLEMENTING", "AUDITING", metrics_root=tmp_path)
        assert (tmp_path / "transitions.jsonl").exists()

    def test_record_fields(self, tmp_path):
        emit_transition(4, "auditor", "IMPLEMENTING", "AUDITING", metrics_root=tmp_path)
        record = json.loads((tmp_path / "transitions.jsonl").read_text(encoding="utf-8"))
        assert record["event"] == "sdd.phase.transition"
        assert record["phase"] == 4
        assert record["role"] == "auditor"
        assert record["from_state"] == "IMPLEMENTING"
        assert record["to_state"] == "AUDITING"
        assert "timestamp" in record

    def test_timestamp_is_iso8601(self, tmp_path):
        emit_transition(4, "auditor", "DRAFT", "REFINED", metrics_root=tmp_path)
        record = json.loads((tmp_path / "transitions.jsonl").read_text(encoding="utf-8"))
        # Should parse without error
        datetime.fromisoformat(record["timestamp"])


class TestEmitTransitionAppend:
    def test_append_only(self, tmp_path):
        emit_transition(3, "auditor", "A", "B", metrics_root=tmp_path)
        emit_transition(4, "implementer", "C", "D", metrics_root=tmp_path)
        lines = (tmp_path / "transitions.jsonl").read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        first = json.loads(lines[0])
        assert first["phase"] == 3  # original line intact


# ---------------------------------------------------------------------------
# emit_audit
# ---------------------------------------------------------------------------


class TestEmitAudit:
    def test_creates_audits_file(self, tmp_path):
        emit_audit(4, "APPROVED", 92.1, 0, metrics_root=tmp_path)
        assert (tmp_path / "audits.jsonl").exists()

    def test_record_fields(self, tmp_path):
        emit_audit(4, "APPROVED", 92.1, 0, test_count=190, metrics_root=tmp_path)
        record = json.loads((tmp_path / "audits.jsonl").read_text(encoding="utf-8"))
        assert record["event"] == "sdd.audit.result"
        assert record["phase"] == 4
        assert record["verdict"] == "APPROVED"
        assert record["coverage_pct"] == 92.1
        assert record["finding_count"] == 0
        assert record["test_count"] == 190

    def test_rejected_verdict(self, tmp_path):
        emit_audit(3, "REJECTED", 60.0, 2, metrics_root=tmp_path)
        record = json.loads((tmp_path / "audits.jsonl").read_text(encoding="utf-8"))
        assert record["verdict"] == "REJECTED"
        assert record["finding_count"] == 2


# ---------------------------------------------------------------------------
# Fail-open
# ---------------------------------------------------------------------------


class TestFailOpen:
    def test_unwritable_path_does_not_raise(self):
        bad_root = Path("/nonexistent/path/that/cannot/exist/ever")
        # Must not raise
        emit_transition(1, "x", "A", "B", metrics_root=bad_root)
        emit_audit(1, "APPROVED", 90.0, 0, metrics_root=bad_root)

    def test_absent_metrics_dir_returns_empty(self, tmp_path):
        empty = tmp_path / "no-metrics"
        assert query_transitions(metrics_root=empty) == []
        assert query_audits(metrics_root=empty) == []


# ---------------------------------------------------------------------------
# query_transitions
# ---------------------------------------------------------------------------


class TestQueryTransitions:
    def _seed(self, root: Path) -> None:
        emit_transition(3, "auditor", "A", "B", metrics_root=root)
        emit_transition(4, "auditor", "B", "C", metrics_root=root)
        emit_transition(4, "implementer", "C", "D", metrics_root=root)

    def test_no_filter_returns_all(self, tmp_path):
        self._seed(tmp_path)
        assert len(query_transitions(metrics_root=tmp_path)) == 3

    def test_phase_filter(self, tmp_path):
        self._seed(tmp_path)
        results = query_transitions(phase=4, metrics_root=tmp_path)
        assert len(results) == 2
        assert all(r["phase"] == 4 for r in results)

    def test_phase_filter_no_match(self, tmp_path):
        self._seed(tmp_path)
        assert query_transitions(phase=99, metrics_root=tmp_path) == []

    def test_since_filter(self, tmp_path):
        # Write a record with a past timestamp manually
        old_record = {
            "event": "sdd.phase.transition",
            "timestamp": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
            "phase": 3, "role": "auditor", "from_state": "A", "to_state": "B",
        }
        (tmp_path / "transitions.jsonl").write_text(
            json.dumps(old_record) + "\n", encoding="utf-8"
        )
        emit_transition(4, "auditor", "C", "D", metrics_root=tmp_path)
        since = datetime.now(UTC) - timedelta(hours=1)
        results = query_transitions(since=since, metrics_root=tmp_path)
        assert len(results) == 1
        assert results[0]["phase"] == 4

    def test_since_naive_datetime(self, tmp_path):
        """since without tzinfo should still work (gets UTC applied)."""
        emit_transition(4, "auditor", "A", "B", metrics_root=tmp_path)
        since = datetime.now() - timedelta(hours=1)  # naive
        results = query_transitions(since=since, metrics_root=tmp_path)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# query_audits
# ---------------------------------------------------------------------------


class TestQueryAudits:
    def test_phase_filter(self, tmp_path):
        emit_audit(3, "REJECTED", 60.0, 2, metrics_root=tmp_path)
        emit_audit(4, "APPROVED", 92.0, 0, metrics_root=tmp_path)
        results = query_audits(phase=4, metrics_root=tmp_path)
        assert len(results) == 1
        assert results[0]["verdict"] == "APPROVED"

    def test_no_filter(self, tmp_path):
        emit_audit(3, "REJECTED", 60.0, 1, metrics_root=tmp_path)
        emit_audit(4, "APPROVED", 92.0, 0, metrics_root=tmp_path)
        assert len(query_audits(metrics_root=tmp_path)) == 2


# ---------------------------------------------------------------------------
# Named acceptance-test functions (must match PHASE_5_CONTRACT.yaml names)
# ---------------------------------------------------------------------------


def test_emit_transition_writes_jsonl(tmp_path):
    """emit_transition creates transitions.jsonl with a valid JSON record."""
    emit_transition(4, "auditor", "IMPLEMENTING", "AUDITING", metrics_root=tmp_path)
    path = tmp_path / "transitions.jsonl"
    assert path.exists()
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["phase"] == 4
    assert record["from_state"] == "IMPLEMENTING"
    assert record["to_state"] == "AUDITING"
    assert record["event"] == "sdd.phase.transition"


def test_emit_audit_writes_jsonl(tmp_path):
    """emit_audit creates audits.jsonl with a valid JSON record."""
    emit_audit(4, "APPROVED", 92.1, 0, metrics_root=tmp_path)
    path = tmp_path / "audits.jsonl"
    assert path.exists()
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["phase"] == 4
    assert record["verdict"] == "APPROVED"
    assert record["coverage_pct"] == 92.1


def test_emit_is_append_only(tmp_path):
    """emit_transition appends; original line remains intact."""
    emit_transition(3, "auditor", "A", "B", metrics_root=tmp_path)
    original_line = (tmp_path / "transitions.jsonl").read_text(encoding="utf-8").strip()
    emit_transition(4, "implementer", "C", "D", metrics_root=tmp_path)
    lines = (tmp_path / "transitions.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert lines[0] == original_line


def test_emit_fail_open_on_unwritable_dir():
    """emit_transition with a bad path must not raise."""
    bad = Path("/nonexistent/cannot/create/this")
    emit_transition(1, "x", "A", "B", metrics_root=bad)  # must not raise


def test_query_transitions_no_filter(tmp_path):
    """query_transitions() with no filters returns all records."""
    for i in range(3):
        emit_transition(3 + i % 2, "auditor", "A", "B", metrics_root=tmp_path)
    assert len(query_transitions(metrics_root=tmp_path)) == 3


def test_query_transitions_phase_filter(tmp_path):
    """query_transitions(phase=4) returns only phase-4 entries."""
    emit_transition(3, "auditor", "A", "B", metrics_root=tmp_path)
    emit_transition(4, "auditor", "C", "D", metrics_root=tmp_path)
    emit_transition(4, "implementer", "D", "E", metrics_root=tmp_path)
    results = query_transitions(phase=4, metrics_root=tmp_path)
    assert len(results) == 2
    assert all(r["phase"] == 4 for r in results)


def test_query_transitions_since_filter(tmp_path):
    """query_transitions(since=T-1h) returns only recent entries."""
    old = {
        "event": "sdd.phase.transition",
        "timestamp": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
        "phase": 3, "role": "a", "from_state": "X", "to_state": "Y",
    }
    (tmp_path / "transitions.jsonl").write_text(json.dumps(old) + "\n", encoding="utf-8")
    emit_transition(4, "auditor", "A", "B", metrics_root=tmp_path)
    results = query_transitions(since=datetime.now(UTC) - timedelta(hours=1), metrics_root=tmp_path)
    assert len(results) == 1
    assert results[0]["phase"] == 4
