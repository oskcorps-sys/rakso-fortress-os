"""Tests for sdd/git_integration.py — git helper functions."""

import subprocess
from pathlib import Path

import pytest

from sdd.git_integration import (
    create_branch,
    get_current_branch,
    is_git_repo,
    is_tree_clean,
    stage_and_commit,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init_repo(root: Path) -> None:
    """Initialise a git repo with an initial commit so HEAD is valid."""
    subprocess.run(["git", "init"], cwd=str(root), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@t.com"], cwd=str(root), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(root), capture_output=True, check=True)
    (root / "init.txt").write_text("init", encoding="utf-8")
    subprocess.run(["git", "add", "init.txt"], cwd=str(root), capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=str(root), capture_output=True, check=True)


# ---------------------------------------------------------------------------
# is_git_repo
# ---------------------------------------------------------------------------


class TestIsGitRepo:
    def test_git_repo_returns_true(self, tmp_path):
        _init_repo(tmp_path)
        assert is_git_repo(tmp_path) is True

    def test_non_repo_returns_false(self, tmp_path):
        assert is_git_repo(tmp_path) is False

    def test_current_project_is_a_repo(self):
        # The SDD+ project itself is a git repo
        assert is_git_repo(Path.cwd()) is True


# ---------------------------------------------------------------------------
# get_current_branch
# ---------------------------------------------------------------------------


class TestGetCurrentBranch:
    def test_returns_branch_name(self, tmp_path):
        _init_repo(tmp_path)
        branch = get_current_branch(tmp_path)
        assert branch != ""
        # Default branch is 'master' or 'main' depending on git config
        assert branch in ("master", "main")

    def test_returns_empty_string_for_non_repo(self, tmp_path):
        assert get_current_branch(tmp_path) == ""

    def test_feature_branch(self, tmp_path):
        _init_repo(tmp_path)
        subprocess.run(["git", "checkout", "-b", "feature/test"], cwd=str(tmp_path), capture_output=True)
        assert get_current_branch(tmp_path) == "feature/test"


# ---------------------------------------------------------------------------
# is_tree_clean
# ---------------------------------------------------------------------------


class TestIsTreeClean:
    def test_clean_tree(self, tmp_path):
        _init_repo(tmp_path)
        assert is_tree_clean(tmp_path) is True

    def test_dirty_tree_untracked(self, tmp_path):
        _init_repo(tmp_path)
        (tmp_path / "dirty.txt").write_text("dirty", encoding="utf-8")
        assert is_tree_clean(tmp_path) is False

    def test_dirty_tree_modified(self, tmp_path):
        _init_repo(tmp_path)
        (tmp_path / "init.txt").write_text("modified", encoding="utf-8")
        assert is_tree_clean(tmp_path) is False

    def test_non_repo_returns_false(self, tmp_path):
        assert is_tree_clean(tmp_path) is False


# ---------------------------------------------------------------------------
# create_branch
# ---------------------------------------------------------------------------


class TestCreateBranch:
    def test_creates_branch(self, tmp_path):
        _init_repo(tmp_path)
        result = create_branch("feature/phase-5", tmp_path)
        assert result["success"] is True
        assert result["branch"] == "feature/phase-5"
        assert get_current_branch(tmp_path) == "feature/phase-5"

    def test_duplicate_branch_fails(self, tmp_path):
        _init_repo(tmp_path)
        create_branch("feature/dupe", tmp_path)
        # Go back to master/main first
        subprocess.run(["git", "checkout", "-"], cwd=str(tmp_path), capture_output=True)
        result = create_branch("feature/dupe", tmp_path)
        assert result["success"] is False
        assert result["branch"] == "feature/dupe"

    def test_not_a_repo_fails(self, tmp_path):
        result = create_branch("feature/x", tmp_path)
        assert result["success"] is False


# ---------------------------------------------------------------------------
# stage_and_commit
# ---------------------------------------------------------------------------


class TestStageAndCommit:
    def test_commits_file(self, tmp_path):
        _init_repo(tmp_path)
        f = tmp_path / "artifact.yaml"
        f.write_text("phase: 5\n", encoding="utf-8")
        result = stage_and_commit("test: add artifact", ["artifact.yaml"], tmp_path)
        assert result["success"] is True
        assert result["sha"] != ""
        # File should be committed
        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )
        assert "test: add artifact" in log.stdout

    def test_not_a_repo_fails(self, tmp_path):
        result = stage_and_commit("msg", ["file.txt"], tmp_path)
        assert result["success"] is False

    def test_nonexistent_file_fails(self, tmp_path):
        _init_repo(tmp_path)
        result = stage_and_commit("msg", ["nonexistent.yaml"], tmp_path)
        assert result["success"] is False
