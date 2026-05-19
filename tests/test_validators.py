"""Tests for validators."""

import pytest
import tempfile
import yaml
from pathlib import Path
from sdd.validators.validate_contract import validate_contract
from sdd.validators.validate_state import validate_state


class TestValidateContractValidator:
    """Tests for validate_contract function."""

    def test_validate_contract_with_dict(self):
        """Test validator with dict input."""
        data = {
            "phase": 1,
            "created_at": "2026-05-19T18:00:00",
            "contract_id": "test-1",
            "status": "DRAFT",
            "specification": {"title": "Test"},
        }
        result = validate_contract(data)
        assert result.valid is True
        assert len(result.errors) == 0
        assert result.schema == "contract"

    def test_validate_contract_invalid_dict(self):
        """Test validator with invalid dict."""
        data = {
            "phase": 1,
            # Missing created_at
            "contract_id": "test-1",
        }
        result = validate_contract(data)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_contract_file_not_found(self):
        """Test validator with non-existent file."""
        result = validate_contract("/nonexistent/path.yaml")
        assert result.valid is False
        assert "File not found" in result.errors[0].message

    def test_validate_contract_with_file(self):
        """Test validator with actual file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            data = {
                "phase": 1,
                "created_at": "2026-05-19T18:00:00",
                "contract_id": "test-2",
                "status": "COMMITTED",
                "specification": {"title": "File test"},
            }
            yaml.dump(data, f)
            f.flush()

            result = validate_contract(f.name)
            assert result.valid is True
            Path(f.name).unlink()


class TestValidateStateValidator:
    """Tests for validate_state function."""

    def test_validate_state_with_dict(self):
        """Test state validator with dict."""
        data = {
            "phase": 1,
            "created_at": "2026-05-19T18:00:00",
            "current_phase": 1,
            "current_state": "DRAFT",
        }
        result = validate_state(data)
        assert result.valid is True
        assert result.schema == "state"

    def test_validate_state_invalid(self):
        """Test state validator with invalid data."""
        data = {
            "phase": 1,
            # Missing created_at
            "current_phase": 1,
        }
        result = validate_state(data)
        assert result.valid is False

    def test_validate_state_file_not_found(self):
        """Test state validator with missing file."""
        result = validate_state("/nonexistent/state.yaml")
        assert result.valid is False


class TestValidatorErrorHandling:
    """Tests for error handling in validators."""

    def test_validator_invalid_yaml_syntax(self):
        """Test validator with malformed YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("{ invalid yaml: [")
            f.flush()

            result = validate_contract(f.name)
            assert result.valid is False
            assert "Invalid YAML" in result.errors[0].message
            Path(f.name).unlink()

    def test_validator_returns_correct_schema_name(self):
        """Test that validator returns correct schema name."""
        data = {
            "phase": 1,
            "created_at": "2026-05-19T18:00:00",
            "contract_id": "test-3",
            "status": "DRAFT",
            "specification": {},
        }
        result = validate_contract(data, schema_name="custom_name")
        assert result.schema == "custom_name"
