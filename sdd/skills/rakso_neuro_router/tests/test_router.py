import json
import pytest
from pydantic import ValidationError

from rakso_neuro_router.models import FunnelStage, NeurofunnelMap, StrategyOutput
from rakso_neuro_router.adapters import (
    TargetAdapter,
    AudioAdapter,
    MockAudioAdapter,
    VisualAdapter,
    MockVisualAdapter,
    DistributionAdapter,
    MockDistributionAdapter,
)
from rakso_neuro_router.router import route
from rakso_neuro_router.validation import validate_no_alteration

# --- Test Custom Adapter Definition ---

class MyCustomOpenSourceAudioAdapter(AudioAdapter):
    local_model_path: str
    sample_rate: int = 22050
    voice_preset: str = "v2/en_speaker_0"
    
    def transform(self, strategy_output: StrategyOutput) -> dict:
        return {
            "model_path": self.local_model_path,
            "settings": {
                "sample_rate": self.sample_rate,
                "voice_preset": self.voice_preset
            },
            "tts_payload": {
                "text": strategy_output.content,
                "metadata": {
                    "stage": strategy_output.neurofunnel_map.funnel_stage.value
                }
            }
        }

# --- 1. Happy Path Tests ---

def test_happy_path_audio_adapter():
    """Verify route returns a valid JSON string mapping the original content correctly for audio."""
    strategy_data = {
        "neurofunnel_map": {"funnel_stage": "AWARENESS"},
        "content": "This is a strictly validated psychological intervention."
    }
    
    adapter = MockAudioAdapter(stability=0.8, similarity_boost=0.7)
    json_payload = route(strategy_data, adapter)
    
    # Assert return is valid JSON
    payload = json.loads(json_payload)
    assert payload["voice_settings"]["stability"] == 0.8
    assert payload["voice_settings"]["similarity_boost"] == 0.7
    assert payload["audio_input"]["text"] == "This is a strictly validated psychological intervention."
    assert payload["audio_input"]["funnel_stage"] == "AWARENESS"


def test_happy_path_visual_adapter():
    """Verify route returns a valid JSON string mapping the original content correctly for visual."""
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.DECISION),
        content= "This is a strictly validated psychological intervention."
    )
    
    adapter = MockVisualAdapter(aspect_ratio="4:3", quality="high", style="cartoon")
    json_payload = route(strategy, adapter)
    
    payload = json.loads(json_payload)
    assert payload["aspect_ratio"] == "4:3"
    assert payload["quality"] == "high"
    assert payload["style"] == "cartoon"
    assert payload["visual_prompt"]["text"] == "This is a strictly validated psychological intervention."
    assert "DECISION" in payload["visual_prompt"]["concept"]


def test_happy_path_distribution_adapter():
    """Verify route returns a valid JSON string mapping the original content correctly for distribution."""
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.ACTION),
        content="This is a strictly validated psychological intervention."
    )
    
    adapter = MockDistributionAdapter(campaign_name="Launch Campaign", platforms=["twitter", "linkedin"])
    json_payload = route(strategy, adapter)
    
    payload = json.loads(json_payload)
    assert payload["campaign"] == "Launch Campaign"
    assert payload["platforms"] == ["twitter", "linkedin"]
    assert payload["publication"]["text"] == "This is a strictly validated psychological intervention."
    assert payload["publication"]["metadata"]["funnel_stage"] == "ACTION"


# --- 2. Edge Cases Tests ---

def test_edge_cases_empty_content():
    """Verify Pydantic ValidationError when content is empty or whitespace-only."""
    with pytest.raises(ValidationError):
        StrategyOutput(
            neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
            content=""
        )

    with pytest.raises(ValidationError):
        StrategyOutput(
            neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
            content="   "
        )


def test_edge_cases_invalid_funnel_stage():
    """Verify Pydantic ValidationError when funnel stage is invalid."""
    with pytest.raises(ValidationError):
        StrategyOutput(
            neurofunnel_map={"funnel_stage": "INVALID_STAGE"},
            content="Valid content string"
        )


def test_edge_cases_invalid_adapter_type():
    """Verify TypeError is raised when adapter is not a TargetAdapter subclass instance."""
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content="Valid content string"
    )
    with pytest.raises(TypeError) as exc_info:
        route(strategy, "Not an adapter")
    assert "adapter_instance must be an instance of a TargetAdapter subclass" in str(exc_info.value)


# --- 3. Custom Adapter Tests ---

def test_custom_adapter():
    """Verify a developer-defined MyCustomOpenSourceAudioAdapter can be routed correctly."""
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.LOYALTY),
        content="This is a strictly validated psychological intervention."
    )
    
    adapter = MyCustomOpenSourceAudioAdapter(
        local_model_path="/models/tts/bark.bin",
        sample_rate=16000,
        voice_preset="v2/en_speaker_9"
    )
    
    json_payload = route(strategy, adapter)
    payload = json.loads(json_payload)
    
    assert payload["model_path"] == "/models/tts/bark.bin"
    assert payload["settings"]["sample_rate"] == 16000
    assert payload["settings"]["voice_preset"] == "v2/en_speaker_9"
    assert payload["tts_payload"]["text"] == "This is a strictly validated psychological intervention."
    assert payload["tts_payload"]["metadata"]["stage"] == "LOYALTY"


# --- 4. No Alteration Tests ---

class BadOmitAdapter(TargetAdapter):
    """Fails to map the original message text."""
    def transform(self, strategy_output: StrategyOutput) -> dict:
        return {
            "some_metadata": "no text here"
        }

class BadAlteredAdapter(TargetAdapter):
    """Alters the message slightly (hype injection)."""
    def transform(self, strategy_output: StrategyOutput) -> dict:
        return {
            "text": "This is a strictly validated psychological intervention! BUY NOW!"
        }

class BadOmissionAdapter(TargetAdapter):
    """Omits the word 'psychological' from the content."""
    def transform(self, strategy_output: StrategyOutput) -> dict:
        return {
            "text": "This is a strictly validated intervention."
        }

def test_no_alteration_omitted():
    """Verify ValueError is raised if the original content is completely omitted."""
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content="This is a strictly validated psychological intervention."
    )
    adapter = BadOmitAdapter()
    with pytest.raises(ValueError) as exc_info:
        route(strategy, adapter)
    assert "Original message content was omitted or altered" in str(exc_info.value)


def test_no_alteration_altered_hype():
    """Verify ValueError is raised if the original content is altered with hype."""
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content="This is a strictly validated psychological intervention."
    )
    adapter = BadAlteredAdapter()
    with pytest.raises(ValueError) as exc_info:
        route(strategy, adapter)
    assert "Integrity Violation: Suspected message alteration" in str(exc_info.value)


def test_no_alteration_omitted_word():
    """Verify ValueError is raised if a word is omitted from the content causing a high overlap."""
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content="This is a strictly validated psychological intervention."
    )
    adapter = BadOmissionAdapter()
    with pytest.raises(ValueError) as exc_info:
        route(strategy, adapter)
    assert "Integrity Violation: Suspected message alteration" in str(exc_info.value)


def test_validate_no_alteration_various_structures():
    """Directly test validate_no_alteration with various data structures and corner cases."""
    # Test empty original text check
    with pytest.raises(ValueError) as exc_info:
        validate_no_alteration("", {"text": "hello"})
    assert "Original text is empty" in str(exc_info.value)

    # Test happy path with list
    validate_no_alteration("hello world", ["hello world", "other"])

    # Test happy path with set and tuple
    validate_no_alteration("hello world", {"hello world", "other"})
    validate_no_alteration("hello world", ("hello world", "other"))

    # Test exact match as substring (should fail due to substring addition / lack of verbatim copy)
    with pytest.raises(ValueError) as exc_info:
        validate_no_alteration("hello world", {"text": "prefix hello world suffix"})
    assert "Integrity Violation" in str(exc_info.value)

    # Test overlap exactly or less than 50%
    # original: "one two three four five" (5 words)
    # node: "one two" (2 words overlap -> 2/5 = 40% overlap <= 50%). Should not raise error, but since exact match is not found anywhere, it will raise the omission error.
    # To test overlap <= 50% without omission error, let's include the exact match in another field.
    payload_ok = {
        "text": "one two three four five",
        "title": "one two" # 40% overlap - ok
    }
    validate_no_alteration("one two three four five", payload_ok)

    # Test overlap > 50% but not containing exactly
    payload_bad = {
        "text": "one two three four five",
        "title": "one two three" # 3/5 = 60% overlap - should trigger alteration error
    }
    with pytest.raises(ValueError) as exc_info:
        validate_no_alteration("one two three four five", payload_bad)
    assert "Integrity Violation: Suspected message alteration" in str(exc_info.value)

