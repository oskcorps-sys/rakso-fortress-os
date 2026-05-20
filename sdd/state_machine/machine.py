"""State machine for SDD+ workflow."""

import os
import yaml
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, Dict, Any

from sdd.schemas.state import StateSnapshotSchema
from sdd.state_machine.transitions import (
    is_transition_allowed,
    TransitionError,
    ALL_STATES,
    ALL_ROLES,
)


class StateMachine:
    """Manages SDD+ state transitions with role-based authorization."""

    STATE_FILE = "sdd/artifacts/STATE_SNAPSHOT.yaml"

    def __init__(self, state_file: Optional[str] = None, agents_yaml_path: str = "AGENTS.yaml"):
        self.state_file = state_file or self.STATE_FILE
        self.agents_yaml_path = agents_yaml_path
        self._state = None
        self._load_state()

    def _load_state(self) -> None:
        """Load state from STATE_SNAPSHOT.yaml."""
        if not Path(self.state_file).exists():
            raise FileNotFoundError(f"State file not found: {self.state_file}")

        with open(self.state_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self._state = StateSnapshotSchema.model_validate(data)

    def _save_state(self) -> None:
        """Save state to STATE_SNAPSHOT.yaml atomically."""
        state_dict = self._state.model_dump(mode="json", exclude_none=False)

        # Use atomic write: write to temp file, then rename
        state_dir = Path(self.state_file).parent
        state_dir.mkdir(parents=True, exist_ok=True)

        tmp_file = f"{self.state_file}.tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            yaml.dump(state_dict, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        # Atomic rename
        os.replace(tmp_file, self.state_file)

    def get_state(self) -> Dict[str, Any]:
        """Get current state snapshot."""
        return {
            "current_phase": self._state.current_phase,
            "current_state": self._state.current_state,
            "last_updated": self._state.last_updated.isoformat(),
            "completed_phases": self._state.completed_phases,
            "locked_at": self._state.locked_at.isoformat() if self._state.locked_at else None,
        }

    def transition(self, to_state: str, role: str) -> Dict[str, Any]:
        """
        Attempt a state transition.

        Args:
            to_state: Target state
            role: Requester role (implementer or auditor)

        Returns:
            Dict with success flag and transition details

        Raises:
            TransitionError: If transition not allowed for role
            ValueError: If state is invalid
        """
        if to_state not in ALL_STATES:
            raise ValueError(f"Invalid state: {to_state}")
        if role not in ALL_ROLES:
            raise ValueError(f"Invalid role: {role}")

        from_state = self._state.current_state

        # Check if transition is allowed
        is_allowed, allowed_roles = is_transition_allowed(
            from_state, to_state, role, agents_yaml_path=self.agents_yaml_path
        )

        if not is_allowed:
            raise TransitionError(from_state, to_state, role, allowed_roles)

        # Perform transition
        old_state = from_state
        self._state.current_state = to_state
        self._state.last_updated = datetime.now(UTC)

        # Track completed phases on certain transitions
        if to_state == "COMPLETED" and self._state.current_phase not in self._state.completed_phases:
            self._state.completed_phases.append(self._state.current_phase)

        # Set locked_at if transitioning to LOCKED
        if to_state == "LOCKED":
            self._state.locked_at = datetime.now(UTC)

        # Persist to disk
        self._save_state()

        return {
            "success": True,
            "from_state": old_state,
            "to_state": to_state,
            "timestamp": self._state.last_updated.isoformat(),
        }

    def start_new_phase(self, next_phase: int) -> Dict[str, Any]:
        """Start a new phase. Caller must verify current_state == COMPLETED."""
        old_phase = self._state.current_phase
        if old_phase not in self._state.completed_phases:
            self._state.completed_phases.append(old_phase)
        self._state.current_phase = next_phase
        self._state.current_state = "DRAFT"
        self._state.locked_at = None
        self._state.last_updated = datetime.now(UTC)
        self._save_state()
        return {
            "old_phase": old_phase,
            "new_phase": next_phase,
            "timestamp": self._state.last_updated.isoformat(),
        }

    def force_reset_to_draft(self, role: str) -> Dict[str, Any]:
        """
        Emergency reset to DRAFT state (auditor only).

        Args:
            role: Must be 'auditor'

        Returns:
            Dict with reset confirmation
        """
        if role != "auditor":
            raise TransitionError(self._state.current_state, "DRAFT", role, ["auditor"])

        old_state = self._state.current_state
        self._state.current_state = "DRAFT"
        self._state.last_updated = datetime.now(UTC)
        self._save_state()

        return {
            "success": True,
            "from_state": old_state,
            "to_state": "DRAFT",
            "reason": "Emergency reset",
            "timestamp": self._state.last_updated.isoformat(),
        }
