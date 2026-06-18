from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

class FunnelStage(str, Enum):
    AWARENESS = "AWARENESS"
    DESTABILIZATION = "DESTABILIZATION"
    VALIDATION = "VALIDATION"
    PRE_DECISION = "PRE_DECISION"
    BRIDGE = "BRIDGE"

class OutputStatus(str, Enum):
    APPROVED = "APPROVED"
    CONDITIONAL = "CONDITIONAL"
    BLOCKED = "BLOCKED"

class ContextDeclaration(BaseModel):
    project_name: str = Field(..., description="MANDATORY INPUT: Context must be declared.")
    
    @field_validator("project_name")
    def force_default_if_empty(cls, v):
        if not v or v.strip() == "":
            return "DEFAULT RAKSO"
        return v.upper()

class NeurofunnelMap(BaseModel):
    funnel_stage: FunnelStage
    core_emotion: str
    cognitive_bias: str
    psychological_goal: str
    next_expected_action: str

    @field_validator("core_emotion")
    def validate_emotion(cls, v):
        if len(v) < 3:
            raise ValueError("Emotion must be explicitly defined.")
        return v

class StrategyOutput(BaseModel):
    neurofunnel_map: NeurofunnelMap
    content: str
    
    @field_validator("content")
    def block_prohibited_terms(cls, v):
        # LAYER 3: RAKSO CREATIVO - PROHIBITED OUTPUT
        prohibited = [
            "guarantee", "journey", "transformation", "become", 
            "achieve your dreams", "fix your life", "easy", "fast"
        ]
        lower_v = v.lower()
        for p in prohibited:
            if p in lower_v:
                raise ValueError(f"Constraint Violation: Prohibited term '{p}' found in output.")
        return v

class ComplianceDecision(BaseModel):
    status: OutputStatus
    violations_detected: List[str] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    
    def is_executable(self) -> bool:
        return self.status != OutputStatus.BLOCKED
