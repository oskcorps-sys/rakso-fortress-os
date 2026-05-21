"""
sdd/git_integration.py — Lightweight git helpers for SDD+ lifecycle automation.

All functions wrap ``git`` via subprocess.run.  Every helper degrades
gracefully when git is absent or the path is not a repository:
  - predicate functions return False
  - action functions return a dict with ``success=False`` and an error message

No new top-level dependencies: stdlib pathlib + subprocess only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a git command in *cwd*.  Never raises; captures stdout/stderr."""
    try:
        return subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        # git not on PATH — return a fake failed result
        proc = subprocess.CompletedProcess(args, returncode=127, stdout="", stderr="git: not found")
        return proc


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------


def is_git_repo(path: Path | None = None) -> bool:
    """Return True if *path* (default: cwd) is inside a git repository."""
    cwd = path if path is not None else Path.cwd()
    result = _run(["git", "rev-parse", "--is-inside-work-tree"], cwd)
    return result.returncode == 0 and result.stdout.strip() == "true"


def get_current_branch(path: Path | None = None) -> str:
    """Return the current branch name, or empty string on failure."""
    cwd = path if path is not None else Path.cwd()
    result = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def is_tree_clean(path: Path | None = None) -> bool:
    """Return True when the working tree has no uncommitted changes.

    Uses ``git status --porcelain``; an empty output means clean.
    Returns False if not in a repo or git is absent.
    """
    cwd = path if path is not None else Path.cwd()
    result = _run(["git", "status", "--porcelain"], cwd)
    if result.returncode != 0:
        return False
    return result.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------


def create_branch(name: str, path: Path | None = None) -> dict:
    """Create and check out branch *name* in the repository at *path*.

    Returns::

        {
          "success": bool,
          "branch": str,      # name of the created branch
          "message": str,     # human-readable result
        }
    """
    cwd = path if path is not None else Path.cwd()
    result = _run(["git", "checkout", "-b", name], cwd)
    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip()
        return {"success": False, "branch": name, "message": error}
    return {"success": True, "branch": name, "message": f"Branch '{name}' created and checked out"}


def stage_and_commit(
    message: str,
    files: list[str],
    path: Path | None = None,
) -> dict:
    """Stage *files* and create a commit with *message* in the repo at *path*.

    Returns::

        {
          "success": bool,
          "sha": str,         # short commit hash, empty on failure
          "message": str,     # human-readable result
        }
    """
    cwd = path if path is not None else Path.cwd()

    # Stage the files
    stage_result = _run(["git", "add", "--"] + files, cwd)
    if stage_result.returncode != 0:
        error = stage_result.stderr.strip() or stage_result.stdout.strip()
        return {"success": False, "sha": "", "message": f"git add failed: {error}"}

    # Commit
    commit_result = _run(["git", "commit", "-m", message], cwd)
    if commit_result.returncode != 0:
        error = commit_result.stderr.strip() or commit_result.stdout.strip()
        return {"success": False, "sha": "", "message": f"git commit failed: {error}"}

    # Retrieve the short SHA of the new commit
    sha_result = _run(["git", "rev-parse", "--short", "HEAD"], cwd)
    sha = sha_result.stdout.strip() if sha_result.returncode == 0 else ""

    return {
        "success": True,
        "sha": sha,
        "message": f"Committed: {sha} {message[:60]}",
    }
