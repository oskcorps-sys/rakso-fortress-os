from abc import ABC
from typing import Dict, Any, List
from pydantic import Field
from rakso_neuro_router.adapters.base import TargetAdapter
from rakso_neuro_router.models import StrategyOutput

class AudioAdapter(TargetAdapter, ABC):
    """Abstract interface for Audio text-to-speech adapters."""
    stability: float = Field(0.75, ge=0.0, le=1.0)
    similarity_boost: float = Field(0.75, ge=0.0, le=1.0)

class MockAudioAdapter(AudioAdapter):
    """Generic/mock implementation of AudioAdapter for testing."""
    voice_id: str = Field("21m00Tcm4TlvDq8ikWAM")
    model_id: str = Field("eleven_monolingual_v1")

    @property
    def active_copy_paths(self) -> List[str]:
        return ["audio_input.text"]

    @property
    def metadata_paths(self) -> List[str]:
        return ["audio_input.funnel_stage"]

    def transform(self, strategy_output: StrategyOutput) -> Dict[str, Any]:
        return {
            "voice_settings": {
                "stability": self.stability,
                "similarity_boost": self.similarity_boost
            },
            "voice_id": self.voice_id,
            "model_id": self.model_id,
            "audio_input": {
                "text": strategy_output.content,
                "funnel_stage": strategy_output.neurofunnel_map.funnel_stage.value
            }
        }
