"""PHASE_SPEC schema - phase requirements and expectations."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sdd.schemas.base import BaseArtifact


class PhaseSpecSchema(BaseArtifact):
    """PHASE_SPEC.yaml schema - what a phase should deliver."""

    title: str = Field(..., description="Phase title")

    description: str = Field(..., description="Full description of phase scope")

    success_criteria: List[str] = Field(
        default_factory=list,
        description="Success metrics"
    )

    scope: Dict[str, Any] = Field(
        default_factory=dict,
        description="What is included vs deferred"
    )

    inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Requirements from previous phase"
    )

    outputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="What this phase produces"
    )

    constraints: List[str] = Field(
        default_factory=list,
        description="Non-negotiable constraints"
    )

    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions made"
    )

    acceptance_tests: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Tests that validate completion"
    )

    dependencies: List[str] = Field(
        default_factory=list,
        description="Phase dependencies"
    )

    class Config:
        """Pydantic config."""
        extra = "allow"
