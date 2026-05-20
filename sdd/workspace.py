"""Multi-project workspace management."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


WORKSPACE_FILE = "sdd.workspace.yaml"


def find_workspace_file(start: Optional[str] = None) -> Optional[Path]:
    """Walk up from start (or cwd) looking for sdd.workspace.yaml."""
    current = Path(start) if start else Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / WORKSPACE_FILE
        if candidate.exists():
            return candidate
    return None


def load_workspace(path: Optional[str] = None) -> Dict[str, Any]:
    """Load workspace config. Returns empty structure if file not found."""
    ws_path = Path(path) if path else find_workspace_file()
    if ws_path is None or not ws_path.exists():
        return {"version": 1, "projects": []}

    with open(ws_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if "projects" not in data:
        data["projects"] = []
    if "version" not in data:
        data["version"] = 1
    return data


def save_workspace(data: Dict[str, Any], path: Optional[str] = None) -> Path:
    """Save workspace config atomically."""
    if path:
        ws_path = Path(path)
    else:
        ws_path = find_workspace_file()
        if ws_path is None:
            ws_path = Path.cwd() / WORKSPACE_FILE

    tmp = f"{ws_path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    os.replace(tmp, str(ws_path))
    return ws_path


def add_project(name: str, project_path: str, ws_path: Optional[str] = None) -> Dict[str, Any]:
    """Add a project to the workspace."""
    resolved = str(Path(project_path).resolve())
    data = load_workspace(ws_path)

    for proj in data["projects"]:
        if proj.get("path") == resolved:
            raise ValueError(f"Project already registered: {resolved}")

    data["projects"].append({"name": name, "path": resolved})
    save_workspace(data, ws_path)
    return data


def remove_project(project_path: str, ws_path: Optional[str] = None) -> Dict[str, Any]:
    """Remove a project from the workspace by path."""
    resolved = str(Path(project_path).resolve())
    data = load_workspace(ws_path)

    original_count = len(data["projects"])
    data["projects"] = [p for p in data["projects"] if p.get("path") != resolved]

    if len(data["projects"]) == original_count:
        raise ValueError(f"Project not found: {resolved}")

    save_workspace(data, ws_path)
    return data


def list_projects(ws_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all projects with their current state (if available)."""
    data = load_workspace(ws_path)
    results = []

    for proj in data["projects"]:
        entry = {"name": proj["name"], "path": proj["path"]}
        state_file = Path(proj["path"]) / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml"
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state = yaml.safe_load(f)
                entry["phase"] = state.get("current_phase", "?")
                entry["state"] = state.get("current_state", "?")
            except Exception:
                entry["phase"] = "?"
                entry["state"] = "?"
        else:
            entry["phase"] = "-"
            entry["state"] = "no state file"
        results.append(entry)

    return results
