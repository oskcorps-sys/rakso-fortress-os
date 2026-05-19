"""Tests for CLI commands."""

import pytest
import json
import tempfile
import yaml
from pathlib import Path
from datetime import datetime, UTC
from typer.testing import CliRunner
from sdd.cli.main import app

runner = CliRunner()


def _create_state_file(path, state="DRAFT", phase=1, completed=None, locked_at=None):
    data = {
        "phase": phase,
        "created_at": datetime.now(UTC).isoformat(),
        "current_phase": phase,
        "current_state": state,
        "completed_phases": completed or [],
    }
    if locked_at:
        data["locked_at"] = locked_at
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def _create_contract_file(path):
    data = {
        "phase": 1,
        "contract_id": "test-contract-v1",
        "created_at": datetime.now(UTC).isoformat(),
        "status": "DRAFT",
        "specification": {
            "title": "Test Phase 1",
            "description": "Test description",
            "success_criteria": ["Criterion 1"],
        },
        "constraints": [],
        "assumptions": [],
        "acceptance_tests": [],
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


class TestStatusCommand:

    def test_status_shows_current_state(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            _create_state_file(state_file)
            monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_file)

            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "DRAFT" in result.output
            assert "Phase:" in result.output

    def test_status_json_output(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            _create_state_file(state_file, state="REFINED")
            monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_file)

            result = runner.invoke(app, ["status", "--json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["current_state"] == "REFINED"
            assert data["current_phase"] == 1

    def test_status_shows_locked_at(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            locked_ts = datetime.now(UTC).isoformat()
            _create_state_file(state_file, state="LOCKED", locked_at=locked_ts)
            monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_file)

            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "Locked At:" in result.output

    def test_status_file_not_found(self, monkeypatch):
        monkeypatch.setattr(
            "sdd.state_machine.machine.StateMachine.STATE_FILE", "/nonexistent/state.yaml"
        )
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 1


class TestValidateCommand:

    def test_validate_valid_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_file = f"{tmpdir}/CONTRACT.yaml"
            _create_contract_file(contract_file)

            result = runner.invoke(app, ["validate", contract_file])
            assert result.exit_code == 0
            assert "valid" in result.output.lower()

    def test_validate_valid_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            _create_state_file(state_file)

            result = runner.invoke(app, ["validate", state_file])
            assert result.exit_code == 0
            assert "valid" in result.output.lower()

    def test_validate_invalid_missing_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_file = f"{tmpdir}/CONTRACT.yaml"
            Path(invalid_file).parent.mkdir(parents=True, exist_ok=True)
            with open(invalid_file, "w") as f:
                yaml.dump({"phase": 1}, f)

            result = runner.invoke(app, ["validate", invalid_file, "--schema", "contract"])
            assert result.exit_code == 1

    def test_validate_file_not_found(self):
        result = runner.invoke(app, ["validate", "/nonexistent/file.yaml"])
        assert result.exit_code == 1

    def test_validate_explicit_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/mydata.yaml"
            _create_state_file(state_file)

            result = runner.invoke(app, ["validate", state_file, "--schema", "state"])
            assert result.exit_code == 0

    def test_validate_auto_detect_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ambiguous_file = f"{tmpdir}/data.yaml"
            _create_state_file(ambiguous_file)

            result = runner.invoke(app, ["validate", ambiguous_file])
            assert result.exit_code == 1

    def test_validate_unknown_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            _create_state_file(state_file)

            result = runner.invoke(app, ["validate", state_file, "--schema", "unknown"])
            assert result.exit_code == 1


class TestTransitionCommand:

    def test_transition_legal_auditor(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            _create_state_file(state_file)
            monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_file)

            result = runner.invoke(app, ["transition", "REFINED", "--role", "auditor"])
            assert result.exit_code == 0
            assert "successful" in result.output.lower()

    def test_transition_legal_implementer(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            _create_state_file(state_file, state="LOCKED")
            monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_file)

            result = runner.invoke(app, ["transition", "IMPLEMENTING", "--role", "implementer"])
            assert result.exit_code == 0

    def test_transition_illegal_role_lock(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            _create_state_file(state_file, state="REFINED")
            monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_file)

            result = runner.invoke(app, ["transition", "LOCKED", "--role", "implementer"])
            assert result.exit_code == 1
            assert "denied" in result.output.lower()

    def test_transition_illegal_role_complete(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            _create_state_file(state_file, state="AUDITING")
            monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_file)

            result = runner.invoke(app, ["transition", "COMPLETED", "--role", "implementer"])
            assert result.exit_code == 1
            assert "denied" in result.output.lower()

    def test_transition_invalid_state(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            _create_state_file(state_file)
            monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_file)

            result = runner.invoke(app, ["transition", "INVALID", "--role", "auditor"])
            assert result.exit_code == 1

    def test_transition_invalid_role(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            _create_state_file(state_file)
            monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_file)

            result = runner.invoke(app, ["transition", "REFINED", "--role", "hacker"])
            assert result.exit_code == 1

    def test_transition_file_not_found(self, monkeypatch):
        monkeypatch.setattr(
            "sdd.state_machine.machine.StateMachine.STATE_FILE", "/nonexistent/state.yaml"
        )
        result = runner.invoke(app, ["transition", "REFINED", "--role", "auditor"])
        assert result.exit_code == 1


class TestInitCommand:

    def test_init_scaffolds_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = str(Path(tmpdir) / "test_project")
            result = runner.invoke(app, ["init", project_path])
            assert result.exit_code == 0

            project_dir = Path(project_path)
            assert (project_dir / "CONTRACT.yaml").exists()
            assert (project_dir / "STATE_SNAPSHOT.yaml").exists()
            assert (project_dir / ".gitignore").exists()

    def test_init_contract_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = str(Path(tmpdir) / "test_project")
            runner.invoke(app, ["init", project_path])

            with open(Path(project_path) / "CONTRACT.yaml", "r") as f:
                data = yaml.safe_load(f)
            assert data["status"] == "DRAFT"
            assert "specification" in data

    def test_init_state_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = str(Path(tmpdir) / "test_project")
            runner.invoke(app, ["init", project_path])

            with open(Path(project_path) / "STATE_SNAPSHOT.yaml", "r") as f:
                data = yaml.safe_load(f)
            assert data["current_state"] == "DRAFT"
            assert data["current_phase"] == 1

    def test_init_existing_dir_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = str(Path(tmpdir) / "test_project")
            Path(project_path).mkdir()

            result = runner.invoke(app, ["init", project_path])
            assert result.exit_code == 1

    def test_init_force_overwrites(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = str(Path(tmpdir) / "test_project")
            Path(project_path).mkdir()

            result = runner.invoke(app, ["init", project_path, "--force"])
            assert result.exit_code == 0
            assert (Path(project_path) / "CONTRACT.yaml").exists()

    def test_init_gitignore_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = str(Path(tmpdir) / "test_project")
            runner.invoke(app, ["init", project_path])

            with open(Path(project_path) / ".gitignore", "r") as f:
                content = f.read()
            assert "__pycache__" in content
            assert ".venv" in content
