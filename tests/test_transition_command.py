"""Tests for sdd transition --github (Sprint 3)."""

import json
from unittest.mock import patch, MagicMock, call

import pytest
import yaml
from pathlib import Path
from datetime import datetime, UTC
from typer.testing import CliRunner

from sdd.cli.main import app
from sdd.cli.commands.transition import (
    _load_github_config,
    _ensure_state_label,
    _get_open_issues,
    _remove_stale_state_labels,
    _label_github_issues,
)

runner = CliRunner()


def _create_state_file(path, state="DRAFT", phase=1):
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


def _write_agents_yaml(tmp_path, enabled=True, repo="owner/repo"):
    content = f"github_integration:\n  enabled: {str(enabled).lower()}\n"
    if repo:
        content += f"  repo: {repo}\n"
    (tmp_path / "AGENTS.yaml").write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# _load_github_config
# ---------------------------------------------------------------------------

class TestLoadGithubConfigTransition:

    def test_returns_config_when_enabled(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_agents_yaml(tmp_path)
        cfg = _load_github_config()
        assert cfg is not None
        assert cfg["repo"] == "owner/repo"

    def test_returns_none_when_disabled(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_agents_yaml(tmp_path, enabled=False)
        assert _load_github_config() is None

    def test_returns_none_when_repo_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write_agents_yaml(tmp_path, repo=None)
        assert _load_github_config() is None

    def test_returns_none_when_no_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert _load_github_config() is None


# ---------------------------------------------------------------------------
# _ensure_state_label
# ---------------------------------------------------------------------------

class TestEnsureStateLabel:

    def test_creates_label_on_success(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            ok = _ensure_state_label("owner/repo", "IMPLEMENTING")
        assert ok is True
        cmd = mock_run.call_args[0][0]
        assert "gh" in cmd[0]
        assert "sdd:IMPLEMENTING" in cmd

    def test_returns_false_on_failure(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("subprocess.run", return_value=mock_result):
            ok = _ensure_state_label("owner/repo", "IMPLEMENTING")
        assert ok is False

    def test_uses_correct_color_per_state(self):
        from sdd.cli.commands.transition import _STATE_COLORS
        mock_result = MagicMock()
        mock_result.returncode = 0
        for state, expected_color in _STATE_COLORS.items():
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                _ensure_state_label("owner/repo", state)
            cmd = mock_run.call_args[0][0]
            assert expected_color in cmd, f"Color {expected_color} not in cmd for state {state}"

    def test_uses_force_flag(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            _ensure_state_label("owner/repo", "DRAFT")
        cmd = mock_run.call_args[0][0]
        assert "--force" in cmd


# ---------------------------------------------------------------------------
# _get_open_issues
# ---------------------------------------------------------------------------

class TestGetOpenIssues:

    def test_returns_milestone_issues(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{"number": 1}, {"number": 2}])
        with patch("subprocess.run", return_value=mock_result):
            issues = _get_open_issues("owner/repo", "Phase 1")
        assert issues == [1, 2]

    def test_falls_back_to_labelled_issues_when_milestone_empty(self):
        empty = MagicMock()
        empty.returncode = 0
        empty.stdout = json.dumps([])

        labelled = MagicMock()
        labelled.returncode = 0
        labelled.stdout = json.dumps([{"number": 5}, {"number": 6}])

        with patch("subprocess.run", side_effect=[empty, labelled]):
            issues = _get_open_issues("owner/repo", "Phase 1")
        assert issues == [5, 6]

    def test_returns_empty_when_no_issues(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([])
        with patch("subprocess.run", return_value=mock_result):
            issues = _get_open_issues("owner/repo", None)
        assert issues == []

    def test_fail_open_on_gh_error(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            issues = _get_open_issues("owner/repo", "Phase 1")
        assert issues == []


# ---------------------------------------------------------------------------
# _label_github_issues
# ---------------------------------------------------------------------------

class TestLabelGithubIssues:

    def _mock_run_success(self, issues=None):
        """Return a side_effect list: ensure_label OK, get_issues OK, remove+add for each."""
        if issues is None:
            issues = [{"number": 1}]

        ensure = MagicMock(returncode=0, stdout="", stderr="")
        get = MagicMock(returncode=0, stdout=json.dumps(issues), stderr="")
        remove = MagicMock(returncode=0, stdout="", stderr="")
        add = MagicMock(returncode=0, stdout="", stderr="")
        return ensure, get, remove, add

    def test_labels_issues_on_success(self, capsys):
        ensure = MagicMock(returncode=0, stdout="", stderr="")
        get = MagicMock(returncode=0, stdout=json.dumps([{"number": 3}, {"number": 7}]), stderr="")
        edit = MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=[ensure, get] + [edit] * 20):
            _label_github_issues(1, "IMPLEMENTING", {"repo": "owner/repo"})

        captured = capsys.readouterr()
        assert "sdd:IMPLEMENTING" in captured.out
        assert "2/2" in captured.out

    def test_warns_when_no_issues(self, capsys):
        ensure = MagicMock(returncode=0, stdout="", stderr="")
        empty = MagicMock(returncode=0, stdout=json.dumps([]), stderr="")

        with patch("subprocess.run", side_effect=[ensure, empty, empty]):
            _label_github_issues(1, "IMPLEMENTING", {"repo": "owner/repo"})

        captured = capsys.readouterr()
        assert "no open issues" in captured.out

    def test_warns_when_label_creation_fails(self, capsys):
        fail = MagicMock(returncode=1, stdout="", stderr="Forbidden")
        with patch("subprocess.run", return_value=fail):
            _label_github_issues(1, "IMPLEMENTING", {"repo": "owner/repo"})

        captured = capsys.readouterr()
        assert "WARN" in captured.out

    def test_fail_open_on_exception(self, capsys):
        with patch("subprocess.run", side_effect=OSError("gh not found")):
            _label_github_issues(1, "IMPLEMENTING", {"repo": "owner/repo"})  # must not raise
        captured = capsys.readouterr()
        assert "WARN" in captured.out


# ---------------------------------------------------------------------------
# Integration: sdd transition --github
# ---------------------------------------------------------------------------

class TestTransitionGithubFlag:

    def test_github_flag_calls_label_issues(self, tmp_path, monkeypatch):
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="DRAFT", phase=1)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)
        _write_agents_yaml(tmp_path)

        mock_result = MagicMock(returncode=0, stdout=json.dumps([{"number": 1}]), stderr="")

        with patch("subprocess.run", return_value=mock_result):
            result = runner.invoke(app, ["transition", "REFINED", "--role", "auditor", "--github"])

        assert result.exit_code == 0, result.output
        assert "DRAFT -> REFINED" in result.output

    def test_github_flag_skipped_without_config(self, tmp_path, monkeypatch):
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="DRAFT", phase=1)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)
        # No AGENTS.yaml

        with patch("subprocess.run") as mock_run:
            result = runner.invoke(app, ["transition", "REFINED", "--role", "auditor", "--github"])

        assert result.exit_code == 0, result.output
        for c in mock_run.call_args_list:
            args = c[0][0] if c[0] else []
            assert "gh" not in str(args)

    def test_no_github_flag_no_gh_calls(self, tmp_path, monkeypatch):
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="DRAFT", phase=1)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)
        _write_agents_yaml(tmp_path)

        with patch("subprocess.run") as mock_run:
            result = runner.invoke(app, ["transition", "REFINED", "--role", "auditor"])

        assert result.exit_code == 0, result.output
        for c in mock_run.call_args_list:
            args = c[0][0] if c[0] else []
            assert "gh" not in str(args)

    def test_transition_still_succeeds_when_gh_fails(self, tmp_path, monkeypatch):
        """Core transition must succeed even if GitHub ops fail."""
        state_path = str(tmp_path / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
        _create_state_file(state_path, state="DRAFT", phase=1)
        monkeypatch.setattr("sdd.state_machine.machine.StateMachine.STATE_FILE", state_path)
        monkeypatch.chdir(tmp_path)
        _write_agents_yaml(tmp_path)

        with patch("subprocess.run", side_effect=OSError("gh not found")):
            result = runner.invoke(app, ["transition", "REFINED", "--role", "auditor", "--github"])

        assert result.exit_code == 0, result.output
        assert "DRAFT -> REFINED" in result.output
