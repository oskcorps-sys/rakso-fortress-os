"""
Shared pytest fixtures for SDD+ tests.

Fixtures:
  - temp_project: temporary SDD+ project directory
  - sample_contract: example CONTRACT.yaml
  - sample_state: example STATE_SNAPSHOT.yaml
"""

import pytest
from pathlib import Path
import yaml
from typing import Dict, Any


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary SDD+ project structure."""
    # Create directories
    (tmp_path / "sdd" / "artifacts").mkdir(parents=True)
    (tmp_path / "sdd" / "logs").mkdir(parents=True)
    (tmp_path / "sdd" / "schemas").mkdir(parents=True)
    (tmp_path / "sdd" / "validators").mkdir(parents=True)
    (tmp_path / "tests").mkdir(parents=True)
    
    # Create .gitkeep files
    (tmp_path / "sdd" / "logs" / ".gitkeep").touch()
    
    return tmp_path


@pytest.fixture
def sample_contract() -> Dict[str, Any]:
    """Return a valid sample CONTRACT.yaml."""
    return {
        "version": 1.0,
        "phase": 1,
        "contract_id": "contract-phase-1-v1",
        "specification": {
            "title": "Sample contract",
            "description": "A test contract",
            "success_criteria": ["Test passes"],
        },
        "inputs": {
            "test_input": {
                "type": "str",
                "required": True,
                "description": "Test input",
                "example": "test",
            }
        },
        "outputs": {
            "test_output": {
                "type": "dict",
                "description": "Test output",
                "example": {"status": "ok"},
            }
        },
        "constraints": ["No secrets"],
        "assumptions": ["Test environment"],
        "acceptance_tests": [
            {
                "name": "test_happy_path",
                "given": "Valid input",
                "when": "Function called",
                "then": "Returns output",
            }
        ],
    }


@pytest.fixture
def sample_state() -> Dict[str, Any]:
    """Return a valid sample STATE_SNAPSHOT.yaml."""
    return {
        "version": 1.0,
        "current_phase": 1,
        "current_state": "DRAFT",
        "phase_history": [
            {
                "phase": 0,
                "state": "BOOTSTRAP",
                "entered_at": "2025-05-19T00:00:00Z",
                "locked_at": "2025-05-19T02:00:00Z",
                "git_tag": "phase-0-locked",
                "summary": "Bootstrap complete",
            }
        ],
    }
