"""
sdd/web/routes.py -- Route handlers for the SDD+ dashboard.

Pages:
  /               -- workspace overview
  /project/{name} -- project detail (phase timeline, audit history)
  /metrics        -- telemetry data from .sdd-metrics/
  /api/health     -- JSON health check
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from sdd.telemetry import query_audits, query_transitions


def _load_yaml(path: Path) -> dict | None:
    """Safely load a YAML file; return None on any error."""
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as fh:
                return yaml.safe_load(fh)
    except Exception:
        pass
    return None


def _get_state(root: Path) -> dict:
    """Load STATE_SNAPSHOT.yaml or return defaults."""
    data = _load_yaml(root / "sdd" / "artifacts" / "STATE_SNAPSHOT.yaml")
    if data is None:
        return {"current_phase": 0, "current_state": "UNKNOWN", "completed_phases": []}
    return data


def _get_projects(root: Path) -> list[dict]:
    """Load workspace projects list.

    Checks sdd.workspace.yaml and sdd/workspace.yaml.
    Falls back to a single entry for the current directory.
    """
    for name in ("sdd.workspace.yaml", "sdd/workspace.yaml"):
        ws = _load_yaml(root / name)
        if ws and "projects" in ws:
            return ws["projects"]
    # Fallback: treat root as the single project
    state = _get_state(root)
    return [{
        "name": root.name or "current",
        "path": str(root),
        "phase": state.get("current_phase", 0),
        "state": state.get("current_state", "UNKNOWN"),
        "completed_phases": state.get("completed_phases", []),
    }]


def _get_audits_for_project(root: Path) -> list[dict]:
    """Scan sdd/artifacts/ for PHASE_N_AUDIT.yaml files."""
    audits: list[dict] = []
    artifacts = root / "sdd" / "artifacts"
    if not artifacts.exists():
        return audits
    for f in sorted(artifacts.glob("PHASE_*_AUDIT.yaml")):
        data = _load_yaml(f)
        if data:
            audits.append(data)
    return audits


def register_routes(app: FastAPI) -> None:
    """Register all dashboard routes on *app*."""

    templates = app.state.templates

    # ----- /api/health -----

    @app.get("/api/health")
    async def health(request: Request) -> JSONResponse:
        root: Path = app.state.project_root
        state = _get_state(root)
        return JSONResponse({
            "status": "ok",
            "phase": state.get("current_phase", 0),
            "state": state.get("current_state", "UNKNOWN"),
        })

    # ----- / -----

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        root: Path = app.state.project_root
        projects = _get_projects(root)
        # Enrich each project with state data
        enriched = []
        for p in projects:
            proj_path = Path(p.get("path", str(root)))
            state = _get_state(proj_path)
            enriched.append({
                "name": p.get("name", proj_path.name),
                "path": str(proj_path),
                "phase": state.get("current_phase", p.get("phase", 0)),
                "state": state.get("current_state", p.get("state", "UNKNOWN")),
                "completed_phases": state.get("completed_phases", p.get("completed_phases", [])),
                "last_updated": state.get("last_updated", ""),
            })
        return templates.TemplateResponse(
            request, "index.html", {"projects": enriched},
        )

    # ----- /project/{name} -----

    @app.get("/project/{name}", response_class=HTMLResponse)
    async def project_detail(request: Request, name: str) -> HTMLResponse:
        root: Path = app.state.project_root
        projects = _get_projects(root)
        project = None
        for p in projects:
            if p.get("name") == name:
                project = p
                break
        if project is None:
            return HTMLResponse("<h1>404 - Project not found</h1>", status_code=404)

        proj_path = Path(project.get("path", str(root)))
        state = _get_state(proj_path)
        audits = _get_audits_for_project(proj_path)

        return templates.TemplateResponse(
            request, "project.html",
            {
                "project": project,
                "state": state,
                "audits": audits,
            },
        )

    # ----- /metrics -----

    @app.get("/metrics", response_class=HTMLResponse)
    async def metrics(request: Request) -> HTMLResponse:
        root: Path = app.state.project_root
        metrics_root = root / ".sdd-metrics"
        transitions = query_transitions(metrics_root=metrics_root)
        audit_records = query_audits(metrics_root=metrics_root)
        return templates.TemplateResponse(
            request, "metrics.html",
            {
                "transitions": transitions,
                "audits": audit_records,
            },
        )
