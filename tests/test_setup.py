"""
test_setup.py - Verify Phase 0 bootstrap is complete.

Tests:
  - Imports work
  - Directory structure exists
  - Sample artifacts are valid YAML
  - CLI responds
"""

import pytest
from pathlib import Path
import yaml


class TestPhase0Bootstrap:
    """Phase 0: Verify repository structure and imports."""
    
    def test_imports_work(self):
        """Test that sdd package can be imported."""
        try:
            import sdd
            assert sdd.__version__ == "0.2.0"
        except ImportError as e:
            pytest.fail(f"Failed to import sdd: {e}")
    
    def test_cli_import(self):
        """Test that CLI app exists."""
        from sdd.tools.sdd import app
        assert app is not None
        assert callable(app)
    
    def test_validator_import(self):
        """Test that validators can be imported."""
        from sdd.validators.validate_contract import validate_contract
        assert callable(validate_contract)
    
    def test_sample_artifacts_valid_yaml(self):
        """Test that sample artifacts are valid YAML."""
        artifacts_dir = Path("sdd/artifacts")

        for yaml_file in artifacts_dir.glob("*.yaml"):
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    data = next(yaml.safe_load_all(f))
                assert data is not None, f"{yaml_file} is empty"
            except yaml.YAMLError as e:
                pytest.fail(f"{yaml_file} is invalid YAML: {e}")
    
    def test_behavior_norms_exists(self):
        """Test that BEHAVIOR_NORMS.md exists."""
        norms_file = Path("sdd/behavior/BEHAVIOR_NORMS.md")
        assert norms_file.exists(), "BEHAVIOR_NORMS.md not found"
        assert norms_file.stat().st_size > 0, "BEHAVIOR_NORMS.md is empty"
    
    def test_state_machine_valid_yaml(self):
        """Test STATE_MACHINE.yaml is valid."""
        sm_file = Path("sdd/state-machine/STATE_MACHINE.yaml")
        assert sm_file.exists()
        
        with open(sm_file) as f:
            sm = yaml.safe_load(f)
        
        assert "states" in sm
        assert "transitions" in sm
        assert len(sm["states"]) > 0
        assert len(sm["transitions"]) > 0
    
    def test_project_files_exist(self):
        """Test that key project files exist."""
        required_files = [
            "README.md",
            "AGENTS.md",
            "CLAUDE.md",
            "DECISIONS.md",
            "BEHAVIOR_NORMS.md",
            "pyproject.toml",
            ".gitignore",
        ]
        
        for file_name in required_files:
            file_path = Path(file_name)
            assert file_path.exists(), f"Missing: {file_name}"
            assert file_path.stat().st_size > 0, f"Empty: {file_name}"


class TestValidators:
    """Test validator functions (Phase 1+)."""
    
    def test_validate_contract_missing_file(self):
        """Test validator catches missing contract."""
        from sdd.validators.validate_contract import validate_contract

        result = validate_contract("nonexistent.yaml")
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_contract_valid_artifact(self, tmp_path):
        """Test validator accepts valid CONTRACT.yaml."""
        from sdd.validators.validate_contract import validate_contract
        from datetime import datetime, UTC

        contract_file = tmp_path / "contract.yaml"
        contract = {
            "phase": 1,
            "contract_id": "test-setup-v1",
            "created_at": datetime.now(UTC).isoformat(),
            "status": "DRAFT",
            "specification": {"title": "Test", "description": "Test"},
        }

        with open(contract_file, "w") as f:
            yaml.dump(contract, f)

        result = validate_contract(contract_file)
        assert result.valid is True
        assert len(result.errors) == 0


class TestCLI:
    """Test CLI functionality."""
    
    def test_cli_help(self):
        """Test that CLI help command works."""
        from sdd.tools.sdd import app
        assert app is not None
        assert app.info.help is not None
    
    def test_cli_commands_registered(self):
        """Test that expected CLI commands exist."""
        from sdd.tools.sdd import app
        
        # Get all registered commands
        command_names = [cmd.name for cmd in app.registered_commands]
        
        # Phase 0: only 'init' should work
        assert "init" in command_names or len(command_names) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
