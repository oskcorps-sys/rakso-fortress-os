from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict
from rakso_neuro_router.models import StrategyOutput

class TargetAdapter(BaseModel, ABC):
    """Base abstract interface for all target adapters."""
    model_config = ConfigDict(extra="forbid")

    @abstractmethod
    def transform(self, strategy_output: StrategyOutput) -> Dict[str, Any]:
        """Transform the StrategyOutput into the adapter's platform-specific structure."""
        pass

    @property
    def active_copy_paths(self) -> List[str]:
        return []

    @property
    def metadata_paths(self) -> List[str]:
        return []
