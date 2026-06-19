from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict

class FunnelStage(str, Enum):
    AWARENESS = "AWARENESS"
    INTEREST = "INTEREST"
    DECISION = "DECISION"
    ACTION = "ACTION"
    LOYALTY = "LOYALTY"

class NeurofunnelMap(BaseModel):
    funnel_stage: FunnelStage = Field(..., description="The stage of the funnel for this content")
    model_config = ConfigDict(extra="allow")

class StrategyOutput(BaseModel):
    neurofunnel_map: NeurofunnelMap = Field(..., description="Neurofunnel metadata mapping")
    content: str = Field(..., min_length=1, description="Strictly validated core psychological intervention copy")
    model_config = ConfigDict(extra="ignore")

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content must not be empty or whitespace-only")
        return v
