"""
sdd/web/app.py -- FastAPI application factory for the SDD+ dashboard.

The dashboard is read-only: it reads workspace config, state snapshots,
audit artifacts, and .sdd-metrics/ JSONL to render HTML pages.

No database, no auth, no write actions.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_app(project_root: Path | None = None) -> FastAPI:
    """Build and return the FastAPI application.

    *project_root* is the SDD+ project directory.  Defaults to cwd.
    It is stored in ``app.state.project_root`` for route handlers.
    """
    app = FastAPI(title="SDD+ Dashboard", version="0.1.0")
    app.state.project_root = project_root if project_root is not None else Path.cwd()
    app.state.templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    from sdd.web.routes import register_routes

    register_routes(app)
    return app
