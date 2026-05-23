"""Tests for sdd new-phase CLI command."""

import subprocess
from unittest.mock import patch, MagicMock

import pytest
import yaml
from pathlib import Path
from datetime import datetime, UTC
from typer.testing import CliRunner

from sdd.cli.main import app
from sdd.cli.commands.new_phase import (
    _load_github_config,
    _create_github_milestone,
    _create_github_release_draft,
)

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


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(root), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=str(root), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(root), capture_output=True, check=True)
    (root / "init.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "init.txt"], cwd=str(root), capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(root), capture_output=True, check=True)


def test_new_phase_git_flag_creates_branch(tmp_path, monkeypatch):
    """sdd new-phase --git creates a feature/phase-N branch after advancing the phase."""
    _init_git_repo(tmp_path)
    state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
    _create_state_file(state_path, state="COMPLETED", phase=2, completed=[1])
    monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["new-phase", "--role", "auditor", "--git"])
    assert result.exit_code == 0, result.output
    assert "Phase 2 -> Phase 3" in result.output
    assert "feature/phase-3" in result.output

    # Verify the branch was actually created in the git repo
    from sdd.git_integration import get_current_branch
    assert get_current_branch(tmp_path) == "feature/phase-3"


# ---------------------------------------------------------------------------
# GitHub integration tests (Sprint 2)
# ---------------------------------------------------------------------------


class TestLoadGithubConfigNewPhase:
    """Tests for _load_github_config() in new_phase module."""

    def test_returns_config_when_enabled(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        agents = tmp_path / "AGENTS.yaml"
        agents.write_text(
            "github_integration:\n  enabled: true\n  repo: owner/repo\n",
            encoding="utf-8",
        )
        cfg = _load_github_config()
        assert cfg is not None
        assert cfg["repo"] == "owner/repo"

    def test_returns_none_when_disabled(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        agents = tmp_path / "AGENTS.yaml"
        agents.write_text(
            "github_integration:\n  enabled: false\n  repo: owner/repo\n",
            encoding="utf-8",
        )
        assert _load_github_config() is None

    def test_returns_none_when_repo_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        agents = tmp_path / "AGENTS.yaml"
        agents.write_text(
            "github_integration:\n  enabled: true\n",
            encoding="utf-8",
        )
        assert _load_github_config() is None

    def test_returns_none_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert _load_github_config() is None

    def test_returns_none_when_block_absent(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        agents = tmp_path / "AGENTS.yaml"
        agents.write_text("version: 1\n", encoding="utf-8")
        assert _load_github_config() is None


class TestCreateGithubMilestone:
    """Tests for _create_github_milestone()."""

    def test_creates_milestone_on_success(self, capsys):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            _create_github_milestone(3, {"repo": "owner/repo"})
        captured = capsys.readouterr()
        assert "Phase 3" in captured.out
        assert "milestone" in captured.out

    def test_warns_on_gh_failure(self, capsys):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "HTTP 422"
        with patch("subprocess.run", return_value=mock_result):
            _create_github_milestone(3, {"repo": "owner/repo"})
        captured = capsys.readouterr()
        assert "WARN" in captured.out

    def test_fail_open_on_exception(self, capsys):
        with patch("subprocess.run", side_effect=FileNotFoundError("gh not found")):
            _create_github_milestone(3, {"repo": "owner/repo"})  # must not raise
        captured = capsys.readouterr()
        assert "WARN" in captured.out


class TestCreateGithubReleaseDraft:
    """Tests for _create_github_release_draft()."""

    def test_creates_release_draft_on_success(self, capsys):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/owner/repo/releases/tag/phase-2-completed"
        with patch("subprocess.run", return_value=mock_result):
            _create_github_release_draft(2, {"repo": "owner/repo"})
        captured = capsys.readouterr()
        assert "github release draft" in captured.out

    def test_warns_on_gh_failure(self, capsys):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "tag already exists"
        with patch("subprocess.run", return_value=mock_result):
            _create_github_release_draft(2, {"repo": "owner/repo"})
        captured = capsys.readouterr()
        assert "WARN" in captured.out

    def test_fail_open_on_exception(self, capsys):
        with patch("subprocess.run", side_effect=OSError("gh not found")):
            _create_github_release_draft(2, {"repo": "owner/repo"})  # must not raise
        captured = capsys.readouterr()
        assert "WARN" in captured.out

    def test_tag_includes_phase_number(self):
        """Milestone tag uses phase-N-completed format."""
        calls = []
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""

        def capture_call(cmd, **_kwargs):
            calls.append(cmd)
            return mock_result

        with patch("subprocess.run", side_effect=capture_call):
            _create_github_release_draft(5, {"repo": "owner/repo"})

        assert any("phase-5-completed" in str(arg) for arg in calls[0])


class TestNewPhaseGithubFlag:
    """Integration tests for sdd new-phase --github."""

    def _write_agents_yaml(self, tmp_path):
        (tmp_path / "AGENTS.yaml").write_text(
            "github_integration:\n  enabled: true\n  repo: owner/repo\n",
            encoding="utf-8",
        )

    def test_github_flag_calls_milestone_and_release(self, tmp_path, monkeypatch):
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="COMPLETED", phase=2, completed=[1])
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)
        self._write_agents_yaml(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/owner/repo/releases/tag/phase-2-completed"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = runner.invoke(app, ["new-phase", "--role", "auditor", "--github"])

        assert result.exit_code == 0, result.output
        # At least two gh calls should have been made (milestone + release)
        assert mock_run.call_count >= 2

    def test_github_flag_skipped_without_config(self, tmp_path, monkeypatch):
        """--github with no AGENTS.yaml should silently skip GitHub ops."""
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="COMPLETED", phase=2, completed=[1])
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)
        # No AGENTS.yaml

        with patch("subprocess.run") as mock_run:
            result = runner.invoke(app, ["new-phase", "--role", "auditor", "--github"])

        assert result.exit_code == 0, result.output
        # subprocess.run should NOT have been called for gh (only no gh ops)
        for call in mock_run.call_args_list:
            args = call[0][0] if call[0] else []
            assert "gh" not in str(args), "gh should not be called without config"

    def test_github_flag_absent_does_not_call_gh(self, tmp_path, monkeypatch):
        """Without --github flag, no GitHub ops should occur."""
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="COMPLETED", phase=2, completed=[1])
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)
        self._write_agents_yaml(tmp_path)

        with patch("subprocess.run") as mock_run:
            result = runner.invoke(app, ["new-phase", "--role", "auditor"])

        assert result.exit_code == 0, result.output
        for call in mock_run.call_args_list:
            args = call[0][0] if call[0] else []
            assert "gh" not in str(args)
