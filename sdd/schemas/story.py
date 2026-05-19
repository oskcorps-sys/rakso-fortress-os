"""USER_STORY schema - business requirements."""

from typing import Optional, List
from pydantic import BaseModel, Field
from sdd.schemas.base import BaseArtifact


class UserStorySchema(BaseArtifact):
    """USER_STORY.yaml schema - business context and requirements."""

    title: str = Field(..., description="Story title")
    user_persona: str = Field(..., description="Who the user is")
    goal: str = Field(..., description="What they want to achieve")
    why: str = Field(..., description="Why it matters")

    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="Definition of done"
    )

    constraints: List[str] = Field(
        default_factory=list,
        description="Limitations or requirements"
    )

    success_metrics: List[str] = Field(
        default_factory=list,
        description="How to measure success"
    )

    class Config:
        """Pydantic config."""
        extra = "allow"
