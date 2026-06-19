from abc import ABC
from typing import Dict, Any, List
from pydantic import Field
from rakso_neuro_router.adapters.base import TargetAdapter
from rakso_neuro_router.models import StrategyOutput

class DistributionAdapter(TargetAdapter, ABC):
    """Abstract interface for Distribution/Publication adapters."""
    campaign_name: str = Field(...)

class MockDistributionAdapter(DistributionAdapter):
    """Generic/mock implementation of DistributionAdapter for testing."""
    platforms: List[str] = Field(default_factory=lambda: ["mock_social_network"])

    @property
    def active_copy_paths(self) -> List[str]:
        return ["publication.text"]

    @property
    def metadata_paths(self) -> List[str]:
        return ["publication.metadata.funnel_stage", "platforms", "campaign"]

    def transform(self, strategy_output: StrategyOutput) -> Dict[str, Any]:
        return {
            "platforms": self.platforms,
            "campaign": self.campaign_name,
            "publication": {
                "text": strategy_output.content,
                "metadata": {
                    "funnel_stage": strategy_output.neurofunnel_map.funnel_stage.value
                }
            }
        }
