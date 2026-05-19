"""AUDIT_RESULT schema - phase audit findings."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sdd.schemas.base import BaseArtifact, ErrorItem


class AuditFinding(BaseModel):
    """Single audit finding."""

    id: str = Field(..., description="Finding ID")
    category: str = Field(..., description="test_coverage, schema, conformance, security, etc")
    severity: str = Field(..., description="blocker, major, minor")
    title: str = Field(..., description="Short description")
    evidence: str = Field(..., description="What was observed")
    requirement: str = Field(..., description="What the spec says")
    disposition: str = Field(..., description="NEEDS_FIX, NEEDS_JUSTIFICATION, ACKNOWLEDGED")


class AuditResultSchema(BaseArtifact):
    """AUDIT_RESULT.yaml schema - phase audit outcome."""

    phase: int = Field(..., description="Phase number")
    status: str = Field(..., description="IN_PROGRESS, APPROVED, REJECTED")

    spec_ref: str = Field(..., description="Reference to phase spec")

    findings: List[AuditFinding] = Field(
        default_factory=list,
        description="All findings"
    )

    test_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Test outcomes (passed, failed, coverage)"
    )

    conformance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Conformance score and violations"
    )

    recommendation: str = Field(
        ...,
        description="Recommendation for human (APPROVED or REJECTED with rationale)"
    )

    signed_at: Optional[datetime] = Field(None, description="When human approved")

    class Config:
        """Pydantic config."""
        extra = "allow"
