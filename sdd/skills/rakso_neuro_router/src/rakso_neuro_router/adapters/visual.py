from abc import ABC
from typing import Dict, Any, Optional, List
from pydantic import Field
from rakso_neuro_router.adapters.base import TargetAdapter
from rakso_neuro_router.models import StrategyOutput

class VisualAdapter(TargetAdapter, ABC):
    """Abstract interface for Visual image/video generation adapters."""
    aspect_ratio: str = Field("16:9", pattern=r"^\d+:\d+$")
    quality: str = Field("standard")

class MockVisualAdapter(VisualAdapter):
    """Generic/mock implementation of VisualAdapter for testing."""
    style: Optional[str] = Field("photorealistic")

    @property
    def active_copy_paths(self) -> List[str]:
        return ["visual_prompt.text"]

    @property
    def metadata_paths(self) -> List[str]:
        return ["visual_prompt.concept", "aspect_ratio", "quality", "style"]

    def transform(self, strategy_output: StrategyOutput) -> Dict[str, Any]:
        return {
            "aspect_ratio": self.aspect_ratio,
            "quality": self.quality,
            "style": self.style,
            "visual_prompt": {
                "text": strategy_output.content,
                "concept": f"Visualizing {strategy_output.neurofunnel_map.funnel_stage.value} stage"
            }
        }
