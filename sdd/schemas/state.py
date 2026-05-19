"""STATE_SNAPSHOT schema - current project state."""

from typing import Optional, Dict, Any, List
from datetime import datetime, UTC
from pydantic import BaseModel, Field, ConfigDict
from sdd.schemas.base import BaseArtifact


class StateTransition(BaseModel):
    """State machine transition."""

    from_state: str = Field(..., description="Current state")
    to_state: str = Field(..., description="Next state")
    conditions: Optional[Dict[str, Any]] = Field(None)
    action: Optional[str] = Field(None)


class StateSnapshotSchema(BaseArtifact):
    """STATE_SNAPSHOT.yaml schema - current state of project."""

    model_config = ConfigDict(extra="allow")

    current_phase: int = Field(..., description="Current phase number")
    current_state: str = Field(..., description="Current state (DRAFT, REFINED, LOCKED)")

    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))

    completed_phases: List[int] = Field(
        default_factory=list,
        description="Completed phases"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Phase-specific metadata"
    )

    locked_at: Optional[datetime] = Field(None, description="When state was locked")
