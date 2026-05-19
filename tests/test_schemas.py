"""Tests for Pydantic schemas."""

import pytest
from datetime import datetime, UTC
from sdd.schemas.contract import ContractSchema
from sdd.schemas.state import StateSnapshotSchema
from sdd.schemas.story import UserStorySchema
from sdd.schemas.spec import PhaseSpecSchema
from sdd.schemas.audit import AuditResultSchema


class TestContractSchema:
    """Tests for ContractSchema."""

    def test_contract_schema_basic(self):
        """Test basic contract schema creation."""
        data = {
            "phase": 1,
            "created_at": datetime.now(UTC),
            "contract_id": "test-contract-1",
            "status": "DRAFT",
            "specification": {"title": "Test", "description": "Test"},
        }
        contract = ContractSchema.model_validate(data)
        assert contract.contract_id == "test-contract-1"
        assert contract.phase == 1

    def test_contract_schema_missing_required(self):
        """Test that required fields are enforced."""
        data = {
            "phase": 1,
            "created_at": datetime.now(UTC),
            # Missing contract_id
            "status": "DRAFT",
            "specification": {},
        }
        with pytest.raises(Exception):
            ContractSchema.model_validate(data)

    def test_contract_schema_with_inputs_outputs(self):
        """Test contract with inputs and outputs."""
        data = {
            "phase": 1,
            "created_at": datetime.now(UTC),
            "contract_id": "test-1",
            "status": "COMMITTED",
            "specification": {},
            "inputs": {
                "param1": {
                    "type": "str",
                    "required": True,
                    "description": "Test param",
                    "example": "value"
                }
            },
            "outputs": {
                "result": {
                    "type": "dict",
                    "description": "Result",
                    "example": {"status": "ok"}
                }
            }
        }
        contract = ContractSchema.model_validate(data)
        assert len(contract.inputs) == 1
        assert len(contract.outputs) == 1


class TestStateSnapshotSchema:
    """Tests for StateSnapshotSchema."""

    def test_state_snapshot_basic(self):
        """Test basic state snapshot."""
        data = {
            "phase": 1,
            "created_at": datetime.now(UTC),
            "current_phase": 1,
            "current_state": "DRAFT",
        }
        state = StateSnapshotSchema.model_validate(data)
        assert state.current_phase == 1
        assert state.current_state == "DRAFT"

    def test_state_snapshot_completed_phases(self):
        """Test state with completed phases."""
        data = {
            "phase": 2,
            "created_at": datetime.now(UTC),
            "current_phase": 2,
            "current_state": "REFINED",
            "completed_phases": [0, 1],
        }
        state = StateSnapshotSchema.model_validate(data)
        assert len(state.completed_phases) == 2


class TestUserStorySchema:
    """Tests for UserStorySchema."""

    def test_user_story_basic(self):
        """Test basic user story."""
        data = {
            "phase": 1,
            "created_at": datetime.now(UTC),
            "title": "Implement validators",
            "user_persona": "Developer",
            "goal": "Validate artifacts",
            "why": "Ensure spec compliance",
        }
        story = UserStorySchema.model_validate(data)
        assert story.title == "Implement validators"


class TestPhaseSpecSchema:
    """Tests for PhaseSpecSchema."""

    def test_phase_spec_basic(self):
        """Test basic phase spec."""
        data = {
            "phase": 1,
            "created_at": datetime.now(UTC),
            "title": "Phase 1: Schemas",
            "description": "Build validation layer",
        }
        spec = PhaseSpecSchema.model_validate(data)
        assert spec.title == "Phase 1: Schemas"


class TestAuditResultSchema:
    """Tests for AuditResultSchema."""

    def test_audit_result_basic(self):
        """Test basic audit result."""
        data = {
            "phase": 1,
            "created_at": datetime.now(UTC),
            "status": "APPROVED",
            "spec_ref": "sdd/artifacts/PHASE_1_SPEC.yaml",
            "recommendation": "Ready for merge",
        }
        audit = AuditResultSchema.model_validate(data)
        assert audit.status == "APPROVED"
