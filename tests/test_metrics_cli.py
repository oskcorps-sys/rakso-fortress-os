"""Tests for sdd metrics show CLI command."""

import json
from datetime import datetime, UTC, timedelta
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sdd.cli.main import app
from sdd.telemetry import emit_audit, emit_transition

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_transitions(root: Path, phases=(3, 4, 4)) -> None:
    for p in phases:
        emit_transition(p, "auditor", "A", "B", metrics_root=root)


def _seed_audits(root: Path, verdicts=(("APPROVED", 92.0), ("REJECTED", 50.0))) -> None:
    for i, (v, c) in enumerate(verdicts):
        emit_audit(4, v, c, 0, metrics_root=root)


# ---------------------------------------------------------------------------
# sdd metrics show
# ---------------------------------------------------------------------------


class TestMetricsShowCLI:
    def test_no_records_info_message(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["metrics", "show", "--metrics-root", str(tmp_path)])
        assert result.exit_code == 0
        assert "no metrics" in result.output.lower()

    def test_shows_transitions(self, tmp_path, monkeypatch):
        _seed_transitions(tmp_path, phases=(4,))
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["metrics", "show", "--metrics-root", str(tmp_path)])
        assert result.exit_code == 0
        assert "Transitions" in result.output
        assert "phase=4" in result.output

    def test_shows_audits(self, tmp_path, monkeypatch):
        emit_audit(4, "APPROVED", 92.0, 0, metrics_root=tmp_path)
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["metrics", "show", "--metrics-root", str(tmp_path)])
        assert result.exit_code == 0
        assert "Audits" in result.output
        assert "APPROVED" in result.output

    def test_phase_filter(self, tmp_path, monkeypatch):
        _seed_transitions(tmp_path, phases=(3, 4, 4))
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app, ["metrics", "show", "--phase", "4", "--metrics-root", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "phase=3" not in result.output
        assert "phase=4" in result.output

    def test_since_filter_excludes_old(self, tmp_path, monkeypatch):
        # Write an old record manually
        old = {
            "event": "sdd.phase.transition",
            "timestamp": (datetime.now(UTC) - timedelta(hours=5)).isoformat(),
            "phase": 3, "role": "a", "from_state": "X", "to_state": "Y",
        }
        (tmp_path / "transitions.jsonl").write_text(json.dumps(old) + "\n", encoding="utf-8")
        emit_transition(4, "auditor", "A", "B", metrics_root=tmp_path)

        since = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app, ["metrics", "show", "--since", since, "--metrics-root", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "phase=3" not in result.output
        assert "phase=4" in result.output

    def test_invalid_since_exits_1(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(
            app, ["metrics", "show", "--since", "not-a-date", "--metrics-root", str(tmp_path)]
        )
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Integration: transition command emits telemetry
# ---------------------------------------------------------------------------


class TestTransitionCommandEmitsTelemetry:
    def test_transition_writes_jsonl(self, tmp_path, monkeypatch):
        import yaml
        from datetime import datetime, UTC

        # Set up state file
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        Path(state_path).parent.mkdir(parents=True, exist_ok=True)
        state_data = {
            "phase": 5,
            "created_at": datetime.now(UTC).isoformat(),
            "current_phase": 5,
            "current_state": "LOCKED",
            "completed_phases": [0, 1, 2, 3, 4],
        }
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.dump(state_data, f)

        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.setenv("SDD_METRICS_ROOT", str(tmp_path / "metrics"))
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["transition", "IMPLEMENTING", "--role", "implementer"])
        assert result.exit_code == 0

        metrics_dir = tmp_path / "metrics"
        assert metrics_dir.exists()
        records = [json.loads(l) for l in (metrics_dir / "transitions.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(records) == 1
        assert records[0]["to_state"] == "IMPLEMENTING"
        assert records[0]["phase"] == 5


# ---------------------------------------------------------------------------
# Integration: audit command emits telemetry
# ---------------------------------------------------------------------------


class TestAuditCommandEmitsTelemetry:
    def test_audit_writes_jsonl(self, tmp_path, monkeypatch):
        import json as _json
        import yaml
        from unittest.mock import MagicMock

        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        Path(state_path).parent.mkdir(parents=True, exist_ok=True)
        state_data = {
            "phase": 1,
            "created_at": datetime.now(UTC).isoformat(),
            "current_phase": 1,
            "current_state": "AUDITING",
            "completed_phases": [],
        }
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.dump(state_data, f)

        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.setenv("SDD_METRICS_ROOT", str(tmp_path / "metrics"))
        monkeypatch.chdir(tmp_path)

        cov_data = {"totals": {"percent_covered": 91.0}}
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        def mock_run(cmd, **kwargs):
            for arg in cmd:
                if arg.startswith("--cov-report=json:"):
                    with open(arg.split(":", 1)[1], "w", encoding="utf-8") as f:
                        _json.dump(cov_data, f)
            return mock_result

        monkeypatch.setattr("subprocess.run", mock_run)

        result = runner.invoke(app, ["audit", "--role", "auditor", "--phase", "1", "--auto-approve"])
        assert result.exit_code == 0

        metrics_dir = tmp_path / "metrics"
        assert (metrics_dir / "audits.jsonl").exists()
        record = _json.loads((metrics_dir / "audits.jsonl").read_text(encoding="utf-8"))
        assert record["verdict"] == "APPROVED"
        assert record["coverage_pct"] == 91.0


# ---------------------------------------------------------------------------
# Named acceptance-test functions (must match PHASE_5_CONTRACT.yaml names)
# ---------------------------------------------------------------------------


def test_metrics_show_cli(tmp_path, monkeypatch):
    """sdd metrics show prints both transition and audit records."""
    emit_transition(4, "auditor", "A", "B", metrics_root=tmp_path)
    emit_audit(4, "APPROVED", 92.0, 0, metrics_root=tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["metrics", "show", "--metrics-root", str(tmp_path)])
    assert result.exit_code == 0
    assert "Transitions" in result.output
    assert "Audits" in result.output


def test_metrics_show_phase_filter(tmp_path, monkeypatch):
    """sdd metrics show --phase 4 shows only phase-4 records."""
    emit_transition(3, "auditor", "A", "B", metrics_root=tmp_path)
    emit_transition(4, "auditor", "C", "D", metrics_root=tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["metrics", "show", "--phase", "4", "--metrics-root", str(tmp_path)]
    )
    assert result.exit_code == 0
    assert "phase=4" in result.output
    assert "phase=3" not in result.output


def test_transition_command_emits_event(tmp_path, monkeypatch):
    """sdd transition writes a JSONL record to transitions.jsonl."""
    import yaml
    state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
    Path(state_path).parent.mkdir(parents=True, exist_ok=True)
    state_data = {
        "phase": 5, "created_at": datetime.now(UTC).isoformat(),
        "current_phase": 5, "current_state": "LOCKED", "completed_phases": [0, 1, 2, 3, 4],
    }
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f)
    monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
    metrics_dir = tmp_path / "metrics"
    monkeypatch.setenv("SDD_METRICS_ROOT", str(metrics_dir))
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["transition", "IMPLEMENTING", "--role", "implementer"])
    assert result.exit_code == 0
    assert (metrics_dir / "transitions.jsonl").exists()
    record = json.loads((metrics_dir / "transitions.jsonl").read_text(encoding="utf-8"))
    assert record["to_state"] == "IMPLEMENTING"


def test_audit_command_emits_event(tmp_path, monkeypatch):
    """sdd audit writes a JSONL record to audits.jsonl."""
    import json as _json
    import yaml
    from unittest.mock import MagicMock

    state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
    Path(state_path).parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump({"phase": 1, "created_at": datetime.now(UTC).isoformat(),
                   "current_phase": 1, "current_state": "AUDITING", "completed_phases": []}, f)
    monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
    metrics_dir = tmp_path / "metrics"
    monkeypatch.setenv("SDD_METRICS_ROOT", str(metrics_dir))
    monkeypatch.chdir(tmp_path)

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = mock_result.stderr = ""

    def mock_run(cmd, **kwargs):
        for arg in cmd:
            if arg.startswith("--cov-report=json:"):
                with open(arg.split(":", 1)[1], "w", encoding="utf-8") as f:
                    _json.dump({"totals": {"percent_covered": 90.0}}, f)
        return mock_result

    monkeypatch.setattr("subprocess.run", mock_run)

    result = runner.invoke(app, ["audit", "--role", "auditor", "--phase", "1", "--auto-approve"])
    assert result.exit_code == 0
    assert (metrics_dir / "audits.jsonl").exists()
    record = _json.loads((metrics_dir / "audits.jsonl").read_text(encoding="utf-8"))
    assert record["verdict"] == "APPROVED"
