"""Base schemas and common fields for SDD+ artifacts."""

from datetime import datetime, UTC
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class BaseArtifact(BaseModel):
    """Base class for all SDD+ artifacts with common metadata."""

    model_config = ConfigDict(extra="allow")

    phase: int = Field(..., description="Phase number (0-4+)")
    created_at: datetime = Field(..., description="Creation timestamp ISO8601")
    description: Optional[str] = Field(None, description="Human-readable description")


class ErrorItem(BaseModel):
    """Validation error detail."""

    field: str = Field(..., description="Field name where error occurred")
    message: str = Field(..., description="Error message (actionable)")
    value: Optional[Any] = Field(None, description="The invalid value")


class WarningItem(BaseModel):
    """Validation warning detail."""

    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Warning message")


class ValidationResult(BaseModel):
    """Standard validation result format.

    Note: the field is named ``schema_name`` (not ``schema``) because
    ``BaseModel.schema()`` is a built-in Pydantic method and shadowing it
    triggers a UserWarning. The two are otherwise unrelated.
    """

    valid: bool = Field(..., description="True if artifact is valid")
    schema_name: str = Field(..., description="Schema name used (contract, state, etc)")
    errors: List[ErrorItem] = Field(default_factory=list, description="Validation errors")
    warnings: List[WarningItem] = Field(default_factory=list, description="Warnings")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Requirement(BaseModel):
    """Single requirement with acceptance criteria."""

    id: str = Field(..., description="Unique requirement ID")
    title: str = Field(..., description="Short title")
    description: str = Field(..., description="Full description")
