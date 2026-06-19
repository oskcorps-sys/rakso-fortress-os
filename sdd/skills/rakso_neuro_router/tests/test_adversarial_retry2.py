import json
import pytest
from pydantic import ValidationError, BaseModel

from rakso_neuro_router.models import FunnelStage, NeurofunnelMap, StrategyOutput
from rakso_neuro_router.adapters.base import TargetAdapter
from rakso_neuro_router.router import route
from rakso_neuro_router.validation import validate_no_alteration

# --- Mock Adapters for Adversarial Testing ---

class DirectPayloadAdapter(TargetAdapter):
    """An adapter that allows us to return any arbitrary payload dict for testing."""
    payload: dict

    def transform(self, strategy_output: StrategyOutput) -> dict:
        return self.payload


# --- 1. Custom Return Types and Pydantic Model in Payload ---

class CustomPayloadModel(BaseModel):
    text: str


def test_pydantic_model_in_payload_raises_type_error():
    """
    Verify that if the adapter returns a dictionary containing a Pydantic BaseModel instance,
    it passes validation (since serialize_to_clean_primitives handles Pydantic models),
    but ultimately raises a TypeError in route() during the final json.dumps().
    """
    original_text = "This is a strictly validated psychological intervention."
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content=original_text
    )
    
    class CustomModelAdapter(TargetAdapter):
        def transform(self, strategy_output: StrategyOutput) -> dict:
            return {
                "payload_model": CustomPayloadModel(text=strategy_output.content)
            }
            
    adapter = CustomModelAdapter()
    
    # Route should raise TypeError due to standard json.dumps failure on custom objects
    with pytest.raises(TypeError) as exc_info:
        route(strategy, adapter)
    assert "is not JSON serializable" in str(exc_info.value)


# --- 2. Custom Class with __dict__ as Return Type ---

class CustomObjectWithDict:
    def __init__(self, text):
        self.text = text


def test_custom_object_in_payload_raises_type_error():
    """
    Verify that custom classes containing __dict__ pass the recursive validator but
    fail serialization in route().
    """
    original_text = "This is a strictly validated psychological intervention."
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content=original_text
    )
    
    class CustomObjectAdapter(TargetAdapter):
        def transform(self, strategy_output: StrategyOutput) -> dict:
            return {
                "data": CustomObjectWithDict(text=strategy_output.content)
            }
            
    adapter = CustomObjectAdapter()
    
    with pytest.raises(TypeError) as exc_info:
        route(strategy, adapter)
    assert "is not JSON serializable" in str(exc_info.value)


# --- 3. Invalid Inputs Blocking ---

def test_invalid_strategy_output_dict():
    """Verify routing raises ValidationError when given an invalid strategy output dict."""
    invalid_strategy = {
        "neurofunnel_map": {"funnel_stage": "NOT_A_STAGE"},
        "content": "Valid copy content"
    }
    adapter = DirectPayloadAdapter(payload={"text": "Valid copy content"})
    
    with pytest.raises(ValidationError):
        route(invalid_strategy, adapter)


def test_invalid_adapter_type():
    """Verify route raises TypeError when given an invalid adapter instance."""
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content="Valid copy content"
    )
    
    with pytest.raises(TypeError) as exc_info:
        route(strategy, "Not an adapter subclass instance")
    assert "adapter_instance must be an instance of a TargetAdapter subclass" in str(exc_info.value)


def test_empty_or_whitespace_content():
    """Verify that empty or whitespace-only content is rejected at the model level."""
    with pytest.raises(ValidationError):
        StrategyOutput(
            neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
            content=""
        )
    with pytest.raises(ValidationError):
        StrategyOutput(
            neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
            content="     "
        )


# --- 4. Formatting and Punctuation Support ---

def test_punctuation_only_copy_routing():
    """Verify punctuation-only values (e.g. ellipsis, dashes) route correctly without alteration."""
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content="..."
    )
    adapter = DirectPayloadAdapter(payload={"text": "..."})
    res = route(strategy, adapter)
    parsed = json.loads(res)
    assert parsed["text"] == "..."


def test_whitespace_and_tabs_routing():
    """Verify that tab and newline variations pass validation and preserve verbatim text characters."""
    original = "Line 1\nLine 2\twith tabs"
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content=original
    )
    adapter = DirectPayloadAdapter(payload={"text": "Line 1\nLine 2\twith tabs"})
    res = route(strategy, adapter)
    parsed = json.loads(res)
    assert parsed["text"] == original


# --- 5. Homoglyph Attacks & Exact Translation Verification ---

def test_homoglyph_detection_on_active_paths():
    """
    Verify that homoglyphs (e.g., Cyrillic 'а' replacing Latin 'a') are blocked
    even when they look similar.
    """
    original = "validated copy"
    # Replacing 'a' with Cyrillic 'а' (U+0430)
    altered = "v\u0430lid\u0430ted copy"
    
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content=original
    )
    adapter = DirectPayloadAdapter(payload={"text": altered})
    
    with pytest.raises(ValueError) as exc_info:
        route(strategy, adapter)
    assert "Integrity Violation" in str(exc_info.value)
