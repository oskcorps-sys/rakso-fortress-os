"""Tests for sdd new-phase CLI command."""

import pytest
import yaml
from pathlib import Path
from datetime import datetime, UTC
from typer.testing import CliRunner

from sdd.cli.main import app

runner = CliRunner()


def _create_state_file(path, state="COMPLETED", phase=2, completed=None):
    data = {
        "phase": phase,
        "created_at": datetime.now(UTC).isoformat(),
        "current_phase": phase,
        "current_state": state,
        "completed_phases": completed or [],
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


class TestNewPhaseCommand:

    def test_new_phase_succeeds(self, monkeypatch, tmp_path):
        """acceptance: test_new_phase_succeeds"""
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="COMPLETED", phase=2, completed=[1])
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["new-phase", "--role", "auditor"])
        assert result.exit_code == 0
        assert "Phase 2 -> Phase 3" in result.output
        assert "DRAFT" in result.output

        with open(state_path) as f:
            state = yaml.safe_load(f)
        assert state["current_phase"] == 3
        assert state["current_state"] == "DRAFT"
        assert 2 in state["completed_phases"]

    def test_new_phase_creates_contract_template(self, monkeypatch, tmp_path):
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="COMPLETED", phase=1)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["new-phase", "--role", "auditor"])
        assert result.exit_code == 0

        contract_path = tmp_path / "sdd" / "artifacts" / "PHASE_2_CONTRACT.yaml"
        assert contract_path.exists()
        with open(contract_path) as f:
            contract = yaml.safe_load(f)
        assert contract["phase"] == 2
        assert contract["status"] == "DRAFT"

    def test_new_phase_creates_handoff(self, monkeypatch, tmp_path):
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="COMPLETED", phase=1)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)

        runner.invoke(app, ["new-phase", "--role", "auditor"])

        handoff = tmp_path / "sdd" / "handoffs" / "PHASE_1_TO_2.md"
        assert handoff.exists()
        content = handoff.read_text(encoding="utf-8")
        assert "Phase 1" in content
        assert "Phase 2" in content

    def test_new_phase_blocked(self, monkeypatch, tmp_path):
        """acceptance: test_new_phase_blocked"""
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="IMPLEMENTING", phase=2)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)

        result = runner.invoke(app, ["new-phase", "--role", "auditor"])
        assert result.exit_code != 0
        assert "COMPLETED" in result.output or "COMPLETED" in (result.stderr or "")

    def test_new_phase_requires_auditor(self):
        result = runner.invoke(app, ["new-phase", "--role", "implementer"])
        assert result.exit_code != 0
        assert "auditor" in result.output.lower() or "auditor" in (result.stderr or "").lower()

    def test_new_phase_no_state_file(self, monkeypatch):
        monkeypatch.setattr(
            "sdd.state_machine.machine.StateMachine.STATE_FILE",
            "/nonexistent/STATE_SNAPSHOT.yaml",
        )
        result = runner.invoke(app, ["new-phase", "--role", "auditor"])
        assert result.exit_code != 0
