"""Tests for multi-project workspace management."""

import pytest
import tempfile
import yaml
from pathlib import Path
from datetime import datetime, UTC

from sdd.workspace import (
    load_workspace,
    save_workspace,
    add_project,
    remove_project,
    list_projects,
)


class TestWorkspaceLoadSave:

    def test_load_empty_workspace(self):
        data = load_workspace("/nonexistent/sdd.workspace.yaml")
        assert data["version"] == 1
        assert data["projects"] == []

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws_path = f"{tmpdir}/sdd.workspace.yaml"
            data = {"version": 1, "projects": [{"name": "test", "path": "/tmp/test"}]}
            save_workspace(data, ws_path)

            loaded = load_workspace(ws_path)
            assert len(loaded["projects"]) == 1
            assert loaded["projects"][0]["name"] == "test"

    def test_save_atomic_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws_path = f"{tmpdir}/sdd.workspace.yaml"
            save_workspace({"version": 1, "projects": []}, ws_path)
            assert Path(ws_path).exists()
            assert not Path(f"{ws_path}.tmp").exists()


class TestAddProject:

    def test_projects_add(self):
        """acceptance: test_projects_add"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws_path = f"{tmpdir}/sdd.workspace.yaml"
            save_workspace({"version": 1, "projects": []}, ws_path)

            project_dir = Path(tmpdir) / "my-project"
            project_dir.mkdir()

            result = add_project("my-project", str(project_dir), ws_path)
            assert len(result["projects"]) == 1
            assert result["projects"][0]["name"] == "my-project"

    def test_add_duplicate_project_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws_path = f"{tmpdir}/sdd.workspace.yaml"
            save_workspace({"version": 1, "projects": []}, ws_path)

            project_dir = Path(tmpdir) / "proj"
            project_dir.mkdir()

            add_project("proj", str(project_dir), ws_path)
            with pytest.raises(ValueError, match="already registered"):
                add_project("proj", str(project_dir), ws_path)


class TestRemoveProject:

    def test_remove_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws_path = f"{tmpdir}/sdd.workspace.yaml"
            project_dir = Path(tmpdir) / "proj"
            project_dir.mkdir()

            add_project("proj", str(project_dir), ws_path)
            result = remove_project(str(project_dir), ws_path)
            assert len(result["projects"]) == 0

    def test_remove_nonexistent_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws_path = f"{tmpdir}/sdd.workspace.yaml"
            save_workspace({"version": 1, "projects": []}, ws_path)

            with pytest.raises(ValueError, match="not found"):
                remove_project("/nonexistent/proj", ws_path)


class TestListProjects:

    def test_projects_list(self):
        """acceptance: test_projects_list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws_path = f"{tmpdir}/sdd.workspace.yaml"

            # Create two project dirs with state files
            for name, phase, state in [("alpha", 2, "IMPLEMENTING"), ("beta", 1, "DRAFT")]:
                proj_dir = Path(tmpdir) / name
                artifacts = proj_dir / "sdd" / "artifacts"
                artifacts.mkdir(parents=True)
                state_data = {
                    "phase": phase,
                    "created_at": datetime.now(UTC).isoformat(),
                    "current_phase": phase,
                    "current_state": state,
                    "completed_phases": [],
                }
                with open(artifacts / "STATE_SNAPSHOT.yaml", "w") as f:
                    yaml.dump(state_data, f)

                add_project(name, str(proj_dir), ws_path)

            projects = list_projects(ws_path)
            assert len(projects) == 2
            assert projects[0]["name"] == "alpha"
            assert projects[0]["phase"] == 2
            assert projects[0]["state"] == "IMPLEMENTING"
            assert projects[1]["name"] == "beta"
            assert projects[1]["state"] == "DRAFT"

    def test_list_project_without_state_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws_path = f"{tmpdir}/sdd.workspace.yaml"
            proj_dir = Path(tmpdir) / "empty-proj"
            proj_dir.mkdir()
            add_project("empty", str(proj_dir), ws_path)

            projects = list_projects(ws_path)
            assert projects[0]["state"] == "no state file"

    def test_list_empty_workspace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws_path = f"{tmpdir}/sdd.workspace.yaml"
            save_workspace({"version": 1, "projects": []}, ws_path)
            assert list_projects(ws_path) == []


class TestProjectsCLI:
    """CLI-level tests for sdd projects subcommands."""

    def test_projects_list_cli(self, monkeypatch, tmp_path):
        from typer.testing import CliRunner
        from sdd.cli.main import app

        ws_path = str(tmp_path / "sdd.workspace.yaml")
        proj_dir = tmp_path / "my-proj"
        artifacts = proj_dir / "sdd" / "artifacts"
        artifacts.mkdir(parents=True)
        state_data = {
            "phase": 1, "created_at": datetime.now(UTC).isoformat(),
            "current_phase": 1, "current_state": "DRAFT", "completed_phases": [],
        }
        with open(artifacts / "STATE_SNAPSHOT.yaml", "w") as f:
            yaml.dump(state_data, f)
        add_project("my-proj", str(proj_dir), ws_path)

        monkeypatch.setattr("sdd.workspace.find_workspace_file", lambda start=None: Path(ws_path))

        cli_runner = CliRunner()
        result = cli_runner.invoke(app, ["projects", "list"])
        assert result.exit_code == 0
        assert "my-proj" in result.output

    def test_projects_add_cli(self, monkeypatch, tmp_path):
        from typer.testing import CliRunner
        from sdd.cli.main import app

        ws_path = tmp_path / "sdd.workspace.yaml"
        save_workspace({"version": 1, "projects": []}, str(ws_path))
        proj_dir = tmp_path / "new-proj"
        proj_dir.mkdir()

        monkeypatch.setattr("sdd.workspace.find_workspace_file", lambda start=None: ws_path)

        cli_runner = CliRunner()
        result = cli_runner.invoke(app, ["projects", "add", str(proj_dir), "--name", "new-proj"])
        assert result.exit_code == 0
        assert "new-proj" in result.output

    def test_projects_remove_cli(self, monkeypatch, tmp_path):
        from typer.testing import CliRunner
        from sdd.cli.main import app

        ws_path = tmp_path / "sdd.workspace.yaml"
        proj_dir = tmp_path / "rm-proj"
        proj_dir.mkdir()
        save_workspace({"version": 1, "projects": []}, str(ws_path))
        add_project("rm-proj", str(proj_dir), str(ws_path))

        monkeypatch.setattr("sdd.workspace.find_workspace_file", lambda start=None: ws_path)

        cli_runner = CliRunner()
        result = cli_runner.invoke(app, ["projects", "remove", str(proj_dir)])
        assert result.exit_code == 0
        assert "Removed" in result.output
