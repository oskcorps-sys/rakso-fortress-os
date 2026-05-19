"""Tests for state machine."""

import pytest
import tempfile
import yaml
from pathlib import Path
from datetime import datetime, UTC
from sdd.state_machine.machine import StateMachine
from sdd.state_machine.transitions import TransitionError, is_transition_allowed


class TestTransitionTable:
    """Tests for transition validation logic."""

    def test_transition_allowed_draft_to_refined_auditor(self):
        """Test DRAFT → REFINED allowed for auditor."""
        allowed, roles = is_transition_allowed("DRAFT", "REFINED", "auditor")
        assert allowed is True
        assert "auditor" in roles

    def test_transition_allowed_draft_to_refined_implementer(self):
        """Test DRAFT → REFINED allowed for implementer."""
        allowed, roles = is_transition_allowed("DRAFT", "REFINED", "implementer")
        assert allowed is True
        assert "implementer" in roles

    def test_transition_allowed_refined_to_locked_auditor(self):
        """Test REFINED → LOCKED allowed for auditor only."""
        allowed, roles = is_transition_allowed("REFINED", "LOCKED", "auditor")
        assert allowed is True
        assert "auditor" in roles

    def test_transition_denied_refined_to_locked_implementer(self):
        """Test REFINED → LOCKED denied for implementer."""
        allowed, roles = is_transition_allowed("REFINED", "LOCKED", "implementer")
        assert allowed is False
        assert "implementer" not in roles
        assert "auditor" in roles

    def test_transition_allowed_locked_to_implementing_implementer(self):
        """Test LOCKED → IMPLEMENTING allowed for implementer."""
        allowed, roles = is_transition_allowed("LOCKED", "IMPLEMENTING", "implementer")
        assert allowed is True

    def test_transition_allowed_implementing_to_auditing_implementer(self):
        """Test IMPLEMENTING → AUDITING allowed for implementer."""
        allowed, roles = is_transition_allowed("IMPLEMENTING", "AUDITING", "implementer")
        assert allowed is True

    def test_transition_allowed_auditing_to_completed_auditor(self):
        """Test AUDITING → COMPLETED allowed for auditor only."""
        allowed, roles = is_transition_allowed("AUDITING", "COMPLETED", "auditor")
        assert allowed is True

    def test_transition_denied_auditing_to_completed_implementer(self):
        """Test AUDITING → COMPLETED denied for implementer."""
        allowed, roles = is_transition_allowed("AUDITING", "COMPLETED", "implementer")
        assert allowed is False

    def test_transition_allowed_auditing_to_implementing_auditor(self):
        """Test AUDITING → IMPLEMENTING (reject loop) allowed for auditor."""
        allowed, roles = is_transition_allowed("AUDITING", "IMPLEMENTING", "auditor")
        assert allowed is True

    def test_emergency_reset_to_draft_auditor(self):
        """Test emergency reset to DRAFT allowed for auditor."""
        allowed, roles = is_transition_allowed("LOCKED", "DRAFT", "auditor")
        assert allowed is True


class TestStateMachine:
    """Tests for StateMachine class."""

    def create_test_state_file(self, path: str) -> None:
        """Create a test STATE_SNAPSHOT.yaml file."""
        state_data = {
            "phase": 1,
            "created_at": datetime.now(UTC).isoformat(),
            "current_phase": 1,
            "current_state": "DRAFT",
            "completed_phases": [],
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(state_data, f)

    def test_state_machine_loads_state(self):
        """Test state machine loads state from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            self.create_test_state_file(state_file)

            machine = StateMachine(state_file)
            state = machine.get_state()

            assert state["current_phase"] == 1
            assert state["current_state"] == "DRAFT"

    def test_state_machine_transition_allowed(self):
        """Test successful transition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            self.create_test_state_file(state_file)

            machine = StateMachine(state_file)
            result = machine.transition("REFINED", "auditor")

            assert result["success"] is True
            assert result["from_state"] == "DRAFT"
            assert result["to_state"] == "REFINED"

            # Verify state was persisted
            state = machine.get_state()
            assert state["current_state"] == "REFINED"

    def test_state_machine_transition_denied_implementer_locks(self):
        """Test REFINED → LOCKED denied for implementer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            state_data = {
                "phase": 1,
                "created_at": datetime.now(UTC).isoformat(),
                "current_phase": 1,
                "current_state": "REFINED",
                "completed_phases": [],
            }
            Path(state_file).parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, "w") as f:
                yaml.dump(state_data, f)

            machine = StateMachine(state_file)

            with pytest.raises(TransitionError) as exc:
                machine.transition("LOCKED", "implementer")

            assert "implementer" in str(exc.value).lower()
            assert "LOCKED" in str(exc.value)

    def test_state_machine_transition_denied_implementer_completes(self):
        """Test AUDITING → COMPLETED denied for implementer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            state_data = {
                "phase": 1,
                "created_at": datetime.now(UTC).isoformat(),
                "current_phase": 1,
                "current_state": "AUDITING",
                "completed_phases": [],
            }
            Path(state_file).parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, "w") as f:
                yaml.dump(state_data, f)

            machine = StateMachine(state_file)

            with pytest.raises(TransitionError):
                machine.transition("COMPLETED", "implementer")

    def test_state_machine_completed_phase_tracking(self):
        """Test completed phases are tracked on COMPLETED transition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            state_data = {
                "phase": 1,
                "created_at": datetime.now(UTC).isoformat(),
                "current_phase": 1,
                "current_state": "AUDITING",
                "completed_phases": [],
            }
            Path(state_file).parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, "w") as f:
                yaml.dump(state_data, f)

            machine = StateMachine(state_file)
            machine.transition("COMPLETED", "auditor")

            state = machine.get_state()
            assert 1 in state["completed_phases"]

    def test_state_machine_atomic_write(self):
        """Test state persists atomically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            self.create_test_state_file(state_file)

            machine = StateMachine(state_file)
            machine.transition("REFINED", "auditor")

            # Verify file exists and is valid YAML
            with open(state_file, "r") as f:
                saved_data = yaml.safe_load(f)

            assert saved_data["current_state"] == "REFINED"

    def test_state_machine_file_not_found(self):
        """Test error when state file does not exist."""
        with pytest.raises(FileNotFoundError):
            StateMachine("/nonexistent/state.yaml")

    def test_state_machine_invalid_state_name(self):
        """Test error on invalid state name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            self.create_test_state_file(state_file)

            machine = StateMachine(state_file)

            with pytest.raises(ValueError):
                machine.transition("INVALID_STATE", "auditor")

    def test_state_machine_invalid_role_name(self):
        """Test error on invalid role name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            self.create_test_state_file(state_file)

            machine = StateMachine(state_file)

            with pytest.raises(ValueError):
                machine.transition("REFINED", "invalid_role")

    def test_state_machine_force_reset_to_draft(self):
        """Test emergency reset to DRAFT (auditor only)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            state_data = {
                "phase": 1,
                "created_at": datetime.now(UTC).isoformat(),
                "current_phase": 1,
                "current_state": "LOCKED",
                "completed_phases": [],
            }
            Path(state_file).parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, "w") as f:
                yaml.dump(state_data, f)

            machine = StateMachine(state_file)
            result = machine.force_reset_to_draft("auditor")

            assert result["success"] is True
            assert result["from_state"] == "LOCKED"
            assert result["to_state"] == "DRAFT"

            state = machine.get_state()
            assert state["current_state"] == "DRAFT"

    def test_state_machine_force_reset_denied_implementer(self):
        """Test emergency reset denied for implementer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = f"{tmpdir}/STATE_SNAPSHOT.yaml"
            self.create_test_state_file(state_file)

            machine = StateMachine(state_file)

            with pytest.raises(TransitionError):
                machine.force_reset_to_draft("implementer")
