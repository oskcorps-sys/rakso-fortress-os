"""CONTRACT schema - binding specification for phase implementation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from sdd.schemas.base import BaseArtifact


class InputField(BaseModel):
    """Input parameter specification."""

    type: str = Field(..., description="Python type (str, int, dict, list)")
    required: bool = Field(default=True)
    description: str = Field(..., description="What this input does")
    example: Any = Field(..., description="Example value")
    constraints: Optional[str] = Field(None, description="Validation rules")


class OutputField(BaseModel):
    """Output specification."""

    type: str = Field(..., description="Python type")
    description: str = Field(..., description="What this output represents")
    example: Any = Field(..., description="Example value")
    schema_ref: Optional[str] = Field(None, description="Reference to schema file")
    validation_rule: Optional[str] = Field(None)


class AcceptanceTest(BaseModel):
    """Acceptance test definition."""

    name: str = Field(..., description="Test name (test_...)")
    given: str = Field(..., description="Setup/precondition")
    when: str = Field(..., description="Action taken")
    then: str = Field(..., description="Expected result")


class ContractSchema(BaseArtifact):
    """CONTRACT.yaml schema - binding specification."""

    model_config = ConfigDict(extra="allow")

    contract_id: str = Field(..., description="Unique contract ID")
    status: str = Field(..., description="DRAFT or COMMITTED")

    specification: Dict[str, Any] = Field(..., description="What this phase delivers")

    inputs: Dict[str, InputField] = Field(
        default_factory=dict,
        description="Input parameters"
    )

    outputs: Dict[str, OutputField] = Field(
        default_factory=dict,
        description="Output specifications"
    )

    constraints: List[str] = Field(
        default_factory=list,
        description="Non-negotiable constraints"
    )

    assumptions: List[str] = Field(
        default_factory=list,
        description="What we assume is true"
    )

    acceptance_tests: List[AcceptanceTest] = Field(
        default_factory=list,
        description="Tests that must pass"
    )

    defer_to_next_phase: List[str] = Field(
        default_factory=list,
        description="Features deferred with rationale"
    )
