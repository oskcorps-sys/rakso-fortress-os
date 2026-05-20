"""Transition table and role-based authority enforcement."""

import warnings
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from sdd.schemas.agent import AgentsConfigSchema, build_transition_table


class TransitionError(Exception):
    """Raised when a state transition is not allowed."""

    def __init__(self, from_state: str, to_state: str, role: str, allowed_roles: List[str]):
        self.from_state = from_state
        self.to_state = to_state
        self.role = role
        self.allowed_roles = allowed_roles
        message = (
            f"Transition from {from_state} to {to_state} not allowed for role '{role}'. "
            f"Allowed roles: {', '.join(allowed_roles)}"
        )
        super().__init__(message)


# States
DRAFT = "DRAFT"
REFINED = "REFINED"
LOCKED = "LOCKED"
IMPLEMENTING = "IMPLEMENTING"
AUDITING = "AUDITING"
COMPLETED = "COMPLETED"

ALL_STATES = {DRAFT, REFINED, LOCKED, IMPLEMENTING, AUDITING, COMPLETED}

# Roles
IMPLEMENTER = "implementer"
AUDITOR = "auditor"

ALL_ROLES = {IMPLEMENTER, AUDITOR}

# Hardcoded fallback transition table
ALLOWED_TRANSITIONS = {
    (DRAFT, REFINED): [IMPLEMENTER, AUDITOR],
    (REFINED, LOCKED): [AUDITOR],
    (LOCKED, IMPLEMENTING): [IMPLEMENTER],
    (IMPLEMENTING, AUDITING): [IMPLEMENTER],
    (AUDITING, COMPLETED): [AUDITOR],
    (AUDITING, IMPLEMENTING): [AUDITOR],
    (DRAFT, DRAFT): [AUDITOR],
    (REFINED, DRAFT): [AUDITOR],
    (LOCKED, DRAFT): [AUDITOR],
    (IMPLEMENTING, DRAFT): [AUDITOR],
    (AUDITING, DRAFT): [AUDITOR],
    (COMPLETED, DRAFT): [AUDITOR],
}


def load_agents_config(agents_yaml_path: str = "AGENTS.yaml") -> Optional[AgentsConfigSchema]:
    """Load and validate AGENTS.yaml. Returns None if file missing or invalid."""
    path = Path(agents_yaml_path)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return AgentsConfigSchema.model_validate(data)
    except Exception as e:
        warnings.warn(f"Failed to load AGENTS.yaml: {e}", stacklevel=2)
        return None


def get_transition_table(
    agents_yaml_path: str = "AGENTS.yaml",
) -> Dict[Tuple[str, str], List[str]]:
    """Get transition table from AGENTS.yaml, falling back to hardcoded defaults."""
    config = load_agents_config(agents_yaml_path)
    if config is not None:
        return build_transition_table(config)
    return ALLOWED_TRANSITIONS


def is_transition_allowed(
    from_state: str,
    to_state: str,
    role: str,
    agents_yaml_path: str = "AGENTS.yaml",
) -> Tuple[bool, List[str]]:
    """Check if a transition is allowed for a given role."""
    if from_state not in ALL_STATES:
        return False, []
    if to_state not in ALL_STATES:
        return False, []
    if role not in ALL_ROLES:
        return False, []

    table = get_transition_table(agents_yaml_path)
    allowed_roles = table.get((from_state, to_state), [])
    is_allowed = role in allowed_roles
    return is_allowed, allowed_roles
