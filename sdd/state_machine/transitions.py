"""Transition table and role-based authority enforcement."""

from typing import Set, Tuple, List


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

# Transition table: (from_state, to_state) -> [allowed_roles]
ALLOWED_TRANSITIONS = {
    (DRAFT, REFINED): [IMPLEMENTER, AUDITOR],
    (REFINED, LOCKED): [AUDITOR],  # GATE: auditor only
    (LOCKED, IMPLEMENTING): [IMPLEMENTER],
    (IMPLEMENTING, AUDITING): [IMPLEMENTER],
    (AUDITING, COMPLETED): [AUDITOR],  # GATE: auditor only
    (AUDITING, IMPLEMENTING): [AUDITOR],  # reject loop: auditor can send back
    # Emergency reset: any state to DRAFT (auditor only)
    (DRAFT, DRAFT): [AUDITOR],
    (REFINED, DRAFT): [AUDITOR],
    (LOCKED, DRAFT): [AUDITOR],
    (IMPLEMENTING, DRAFT): [AUDITOR],
    (AUDITING, DRAFT): [AUDITOR],
    (COMPLETED, DRAFT): [AUDITOR],
}


def is_transition_allowed(from_state: str, to_state: str, role: str) -> Tuple[bool, List[str]]:
    """
    Check if a transition is allowed for a given role.

    Args:
        from_state: Current state
        to_state: Target state
        role: Requester role (implementer or auditor)

    Returns:
        Tuple of (is_allowed: bool, allowed_roles: List[str])
    """
    if from_state not in ALL_STATES:
        return False, []
    if to_state not in ALL_STATES:
        return False, []
    if role not in ALL_ROLES:
        return False, []

    allowed_roles = ALLOWED_TRANSITIONS.get((from_state, to_state), [])
    is_allowed = role in allowed_roles
    return is_allowed, allowed_roles
