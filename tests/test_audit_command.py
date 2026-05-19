"""Tests for sdd audit CLI command."""

import json
import pytest
import yaml
from pathlib import Path
from datetime import datetime, UTC
from unittest.mock import MagicMock
from typer.testing import CliRunner

from sdd.cli.main import app

runner = CliRunner()


def _create_state_file(path, state="AUDITING", phase=1):
    data = {
        "phase": phase,
        "created_at": datetime.now(UTC).isoformat(),
        "current_phase": phase,
        "current_state": state,
        "completed_phases": [],
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


class TestAuditCommand:

    def test_audit_requires_auditor_role(self):
        result = runner.invoke(app, ["audit", "--role", "implementer"])
        assert result.exit_code != 0
        assert "auditor" in result.output.lower() or "auditor" in (result.stderr or "").lower()

    def test_audit_command_passes(self, monkeypatch, tmp_path):
        """acceptance: test_audit_command_passes"""
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="AUDITING", phase=1)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "all passed"
        mock_result.stderr = ""

        cov_data = {"totals": {"percent_covered": 92.5}}

        def mock_subprocess_run(cmd, **kwargs):
            for arg in cmd:
                if arg.startswith("--cov-report=json:"):
                    cov_path = arg.split(":", 1)[1]
                    with open(cov_path, "w") as f:
                        json.dump(cov_data, f)
            return mock_result

        monkeypatch.setattr("subprocess.run", mock_subprocess_run)

        result = runner.invoke(app, ["audit", "--role", "auditor", "--phase", "1"])
        assert result.exit_code == 0
        assert "APPROVED" in result.output

        audit_file = tmp_path / "sdd" / "artifacts" / "PHASE_1_AUDIT.yaml"
        assert audit_file.exists()
        with open(audit_file) as f:
            audit_data = yaml.safe_load(f)
        assert audit_data["verdict"] == "APPROVED"

    def test_audit_command_fails(self, monkeypatch, tmp_path):
        """acceptance: test_audit_command_fails"""
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="AUDITING", phase=1)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "FAILED"
        mock_result.stderr = "1 failed"

        monkeypatch.setattr("subprocess.run", lambda cmd, **kw: mock_result)

        result = runner.invoke(app, ["audit", "--role", "auditor", "--phase", "1"])
        assert result.exit_code != 0

        audit_file = tmp_path / "sdd" / "artifacts" / "PHASE_1_AUDIT.yaml"
        assert audit_file.exists()
        with open(audit_file) as f:
            audit_data = yaml.safe_load(f)
        assert audit_data["verdict"] == "REJECTED"

    def test_audit_no_state_file(self, monkeypatch):
        monkeypatch.setattr(
            "sdd.state_machine.machine.StateMachine.STATE_FILE",
            "/nonexistent/STATE_SNAPSHOT.yaml",
        )
        result = runner.invoke(app, ["audit", "--role", "auditor"])
        assert result.exit_code != 0

    def test_audit_auto_approve(self, monkeypatch, tmp_path):
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="AUDITING", phase=1)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0

        cov_data = {"totals": {"percent_covered": 90.0}}

        def mock_run(cmd, **kwargs):
            for arg in cmd:
                if arg.startswith("--cov-report=json:"):
                    with open(arg.split(":", 1)[1], "w") as f:
                        json.dump(cov_data, f)
            return mock_result

        monkeypatch.setattr("subprocess.run", mock_run)

        result = runner.invoke(app, [
            "audit", "--role", "auditor", "--phase", "1", "--auto-approve",
        ])
        assert result.exit_code == 0

        audit_file = tmp_path / "sdd" / "artifacts" / "PHASE_1_AUDIT.yaml"
        with open(audit_file) as f:
            audit_data = yaml.safe_load(f)
        assert "signed_at" in audit_data

    def test_audit_spec_conformance_missing_files(self, monkeypatch, tmp_path):
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="AUDITING", phase=1)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)

        spec_data = {
            "scope": {"included": ["nonexistent/file.py — some module", "another/missing.py"]},
        }
        spec_path = tmp_path / "sdd" / "artifacts" / "PHASE_1_SPEC.yaml"
        with open(spec_path, "w") as f:
            yaml.dump(spec_data, f)

        mock_result = MagicMock()
        mock_result.returncode = 0
        cov_data = {"totals": {"percent_covered": 90.0}}

        def mock_run(cmd, **kwargs):
            for arg in cmd:
                if arg.startswith("--cov-report=json:"):
                    with open(arg.split(":", 1)[1], "w") as f:
                        json.dump(cov_data, f)
            return mock_result

        monkeypatch.setattr("subprocess.run", mock_run)

        result = runner.invoke(app, ["audit", "--role", "auditor", "--phase", "1"])
        assert result.exit_code == 0

        audit_file = tmp_path / "sdd" / "artifacts" / "PHASE_1_AUDIT.yaml"
        with open(audit_file) as f:
            audit_data = yaml.safe_load(f)
        assert audit_data["steps"]["spec_conformance"]["passed"] is False
        assert len(audit_data["steps"]["spec_conformance"]["missing_files"]) == 2

    def test_audit_contract_conformance_missing_tests(self, monkeypatch, tmp_path):
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="AUDITING", phase=1)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)

        contract_data = {
            "acceptance_tests": [
                {"name": "test_something_real"},
                {"name": "test_totally_missing"},
            ],
        }
        contract_path = tmp_path / "sdd" / "artifacts" / "PHASE_1_CONTRACT.yaml"
        with open(contract_path, "w") as f:
            yaml.dump(contract_data, f)

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_example.py").write_text(
            "def test_something_real():\n    pass\n", encoding="utf-8"
        )

        mock_result = MagicMock()
        mock_result.returncode = 0
        cov_data = {"totals": {"percent_covered": 90.0}}

        def mock_run(cmd, **kwargs):
            for arg in cmd:
                if arg.startswith("--cov-report=json:"):
                    with open(arg.split(":", 1)[1], "w") as f:
                        json.dump(cov_data, f)
            return mock_result

        monkeypatch.setattr("subprocess.run", mock_run)

        result = runner.invoke(app, ["audit", "--role", "auditor", "--phase", "1"])
        assert result.exit_code == 0

        audit_file = tmp_path / "sdd" / "artifacts" / "PHASE_1_AUDIT.yaml"
        with open(audit_file) as f:
            audit_data = yaml.safe_load(f)
        assert audit_data["steps"]["contract_conformance"]["passed"] is False
        assert "test_totally_missing" in audit_data["steps"]["contract_conformance"]["missing_tests"]

    def test_audit_low_coverage_rejected(self, monkeypatch, tmp_path):
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="AUDITING", phase=1)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0
        cov_data = {"totals": {"percent_covered": 50.0}}

        def mock_run(cmd, **kwargs):
            for arg in cmd:
                if arg.startswith("--cov-report=json:"):
                    with open(arg.split(":", 1)[1], "w") as f:
                        json.dump(cov_data, f)
            return mock_result

        monkeypatch.setattr("subprocess.run", mock_run)

        result = runner.invoke(app, ["audit", "--role", "auditor", "--phase", "1"])
        assert result.exit_code != 0

        audit_file = tmp_path / "sdd" / "artifacts" / "PHASE_1_AUDIT.yaml"
        with open(audit_file) as f:
            audit_data = yaml.safe_load(f)
        assert audit_data["verdict"] == "REJECTED"
        assert audit_data["coverage_percent"] == 50.0
