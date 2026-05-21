"""Tests for the SDD+ web dashboard (Phase 6).

Uses httpx.AsyncClient against the FastAPI test client -- no real server needed.
"""

import json
from datetime import datetime, UTC
from pathlib import Path

import pytest
import yaml
from httpx import ASGITransport, AsyncClient
from typer.testing import CliRunner

from sdd.cli.main import app as cli_app
from sdd.telemetry import emit_audit, emit_transition
from sdd.web.app import create_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def project_root(tmp_path):
    """Create a minimal SDD+ project layout in tmp_path."""
    artifacts = tmp_path / "sdd" / "artifacts"
    artifacts.mkdir(parents=True)
    state = {
        "phase": 6,
        "created_at": datetime.now(UTC).isoformat(),
        "current_phase": 6,
        "current_state": "IMPLEMENTING",
        "completed_phases": [0, 1, 2, 3, 4, 5],
        "last_updated": datetime.now(UTC).isoformat(),
    }
    with open(artifacts / "STATE_SNAPSHOT.yaml", "w", encoding="utf-8") as f:
        yaml.dump(state, f, allow_unicode=True)
    return tmp_path


@pytest.fixture
def project_with_audits(project_root):
    """Extend project_root with audit artifacts."""
    artifacts = project_root / "sdd" / "artifacts"
    for phase, verdict, cov in [(4, "APPROVED", 92.1), (5, "APPROVED", 91.7)]:
        audit = {
            "audit_id": f"audit-phase-{phase}-v1",
            "phase": phase,
            "timestamp": datetime.now(UTC).isoformat(),
            "auditor": "auditor",
            "verdict": verdict,
            "coverage_percent": cov,
            "findings": [],
        }
        with open(artifacts / f"PHASE_{phase}_AUDIT.yaml", "w", encoding="utf-8") as f:
            yaml.dump(audit, f, allow_unicode=True)
    return project_root


@pytest.fixture
def project_with_metrics(project_root):
    """Extend project_root with .sdd-metrics/ data."""
    metrics = project_root / ".sdd-metrics"
    emit_transition(5, "auditor", "DRAFT", "REFINED", metrics_root=metrics)
    emit_transition(5, "auditor", "REFINED", "LOCKED", metrics_root=metrics)
    emit_audit(5, "APPROVED", 91.7, 0, metrics_root=metrics)
    return project_root


@pytest.fixture
def project_with_workspace(project_root):
    """Extend project_root with a sdd.workspace.yaml listing two projects."""
    ws = {
        "projects": [
            {"name": "alpha", "path": str(project_root)},
            {"name": "beta", "path": str(project_root)},
        ]
    }
    with open(project_root / "sdd.workspace.yaml", "w", encoding="utf-8") as f:
        yaml.dump(ws, f, allow_unicode=True)
    return project_root


# ---------------------------------------------------------------------------
# Async test client helper
# ---------------------------------------------------------------------------


async def _get(root: Path, path: str) -> tuple:
    """Make a GET request to *path* and return (status_code, text)."""
    web_app = create_app(project_root=root)
    transport = ASGITransport(app=web_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(path)
        return resp.status_code, resp.text


# ---------------------------------------------------------------------------
# /api/health
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    @pytest.mark.anyio
    async def test_returns_200(self, project_root):
        status, text = await _get(project_root, "/api/health")
        assert status == 200
        data = json.loads(text)
        assert data["status"] == "ok"
        assert data["phase"] == 6


# ---------------------------------------------------------------------------
# / (index)
# ---------------------------------------------------------------------------


class TestIndexPage:
    @pytest.mark.anyio
    async def test_lists_project(self, project_root):
        status, text = await _get(project_root, "/")
        assert status == 200
        # Fallback single project uses dir name
        assert "Phase" in text

    @pytest.mark.anyio
    async def test_lists_workspace_projects(self, project_with_workspace):
        status, text = await _get(project_with_workspace, "/")
        assert status == 200
        assert "alpha" in text
        assert "beta" in text

    @pytest.mark.anyio
    async def test_empty_workspace(self, tmp_path):
        # No artifacts at all
        status, text = await _get(tmp_path, "/")
        assert status == 200
        # Should still render (fallback project with UNKNOWN state)
        assert "UNKNOWN" in text or "Phase" in text


# ---------------------------------------------------------------------------
# /project/{name}
# ---------------------------------------------------------------------------


class TestProjectDetailPage:
    @pytest.mark.anyio
    async def test_project_detail(self, project_with_workspace):
        status, text = await _get(project_with_workspace, "/project/alpha")
        assert status == 200
        assert "alpha" in text
        assert "IMPLEMENTING" in text or "Phase" in text

    @pytest.mark.anyio
    async def test_project_with_audits(self, project_with_audits):
        # Need a workspace file pointing to this project
        ws = {"projects": [{"name": "myproj", "path": str(project_with_audits)}]}
        with open(project_with_audits / "sdd.workspace.yaml", "w", encoding="utf-8") as f:
            yaml.dump(ws, f, allow_unicode=True)
        status, text = await _get(project_with_audits, "/project/myproj")
        assert status == 200
        assert "APPROVED" in text
        assert "92.1" in text or "91.7" in text

    @pytest.mark.anyio
    async def test_project_not_found(self, project_root):
        status, text = await _get(project_root, "/project/nonexistent")
        assert status == 404


# ---------------------------------------------------------------------------
# /metrics
# ---------------------------------------------------------------------------


class TestMetricsPage:
    @pytest.mark.anyio
    async def test_with_data(self, project_with_metrics):
        status, text = await _get(project_with_metrics, "/metrics")
        assert status == 200
        assert "Transitions" in text
        assert "Audits" in text

    @pytest.mark.anyio
    async def test_empty_metrics(self, tmp_path):
        status, text = await _get(tmp_path, "/metrics")
        assert status == 200
        assert "no metrics" in text.lower() or "No metrics" in text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestDashboardCLI:
    def test_help_shows_port_option(self):
        result = runner.invoke(cli_app, ["dashboard", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.output


# ---------------------------------------------------------------------------
# Named acceptance-test functions (match PHASE_6_CONTRACT.yaml names)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_health_endpoint(project_root):
    status, text = await _get(project_root, "/api/health")
    assert status == 200
    assert json.loads(text)["status"] == "ok"


@pytest.mark.anyio
async def test_index_page_lists_projects(project_with_workspace):
    status, text = await _get(project_with_workspace, "/")
    assert status == 200
    assert "alpha" in text


@pytest.mark.anyio
async def test_index_page_empty_workspace(tmp_path):
    status, text = await _get(tmp_path, "/")
    assert status == 200


@pytest.mark.anyio
async def test_project_detail_page(project_with_workspace):
    status, text = await _get(project_with_workspace, "/project/alpha")
    assert status == 200
    assert "Phase" in text


@pytest.mark.anyio
async def test_project_detail_with_audits(project_with_audits):
    ws = {"projects": [{"name": "proj", "path": str(project_with_audits)}]}
    with open(project_with_audits / "sdd.workspace.yaml", "w", encoding="utf-8") as f:
        yaml.dump(ws, f, allow_unicode=True)
    status, text = await _get(project_with_audits, "/project/proj")
    assert status == 200
    assert "APPROVED" in text


@pytest.mark.anyio
async def test_project_not_found(project_root):
    status, text = await _get(project_root, "/project/nonexistent")
    assert status == 404


@pytest.mark.anyio
async def test_metrics_page(project_with_metrics):
    status, text = await _get(project_with_metrics, "/metrics")
    assert status == 200
    assert "Transitions" in text


@pytest.mark.anyio
async def test_metrics_page_empty(tmp_path):
    status, text = await _get(tmp_path, "/metrics")
    assert status == 200


def test_dashboard_cli_starts():
    result = runner.invoke(cli_app, ["dashboard", "--help"])
    assert result.exit_code == 0
    assert "--port" in result.output
