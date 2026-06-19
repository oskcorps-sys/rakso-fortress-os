import json
import pytest
from pydantic import ValidationError

from rakso_neuro_router.models import FunnelStage, NeurofunnelMap, StrategyOutput
from rakso_neuro_router.adapters.base import TargetAdapter
from rakso_neuro_router.router import route
from rakso_neuro_router.validation import validate_no_alteration

# --- Mock Adapters for Stress Testing ---

class DirectPayloadAdapter(TargetAdapter):
    """An adapter that allows us to return any arbitrary payload dict for testing."""
    payload: dict

    def transform(self, strategy_output: StrategyOutput) -> dict:
        return self.payload


# --- 1. String Subclass Bypass (Critical Security Vulnerability) ---

class BypassStr(str):
    """A string subclass that overrides comparison to always return True."""
    def __eq__(self, other):
        return True
    
    def __contains__(self, other):
        return True


def test_string_subclass_bypass():
    """
    Verify that string subclass bypass attempts are successfully blocked and raise ValueError.
    """
    original_text = "This is a strictly validated psychological intervention."
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content=original_text
    )
    
    altered_text = BypassStr("Hacked and altered text! BUY NOW! HYPE!")
    adapter = DirectPayloadAdapter(payload={"output_text": altered_text})
    
    with pytest.raises(ValueError) as exc_info:
        route(strategy, adapter)
    assert "Integrity Violation" in str(exc_info.value)


# --- 2. Dictionary Subclass Bypass (Critical Security Vulnerability) ---

class BypassDict(dict):
    """A dict subclass that overrides values() to hide the actual payload content during walk."""
    def values(self):
        return ["This is a strictly validated psychological intervention."]


def test_dict_subclass_bypass():
    """
    Verify that dictionary subclass bypass attempts are successfully blocked and raise ValueError.
    """
    original_text = "This is a strictly validated psychological intervention."
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content=original_text
    )
    
    bypass_payload = BypassDict({"output_text": "BUY NOW! Altered text!"})
    adapter = DirectPayloadAdapter(payload=bypass_payload)
    
    with pytest.raises(ValueError) as exc_info:
        route(strategy, adapter)
    assert "Integrity Violation" in str(exc_info.value)


# --- 3. Homoglyph / Unicode Lookalike Bypass ---

def test_homoglyph_bypass():
    """
    Verify that homoglyphs (lookalike characters) in the active field raise ValueError
    even if the exact copy is in a dummy field.
    """
    original_text = "therapy"
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content=original_text
    )
    
    # 'therapy' but with Cyrillic 'е' (U+0435) and 'а' (U+0430)
    homoglyph_text = "thеrаpy" 
    
    payload = {
        "dummy_field": original_text, # exact ASCII copy
        "active_text": homoglyph_text # Cyrillic lookalike
    }
    adapter = DirectPayloadAdapter(payload=payload)
    
    with pytest.raises(ValueError) as exc_info:
        route(strategy, adapter)
    assert "Integrity Violation" in str(exc_info.value)
    assert "homoglyph" in str(exc_info.value).lower() or "character-level mismatch" in str(exc_info.value).lower()


# --- 4. Low-Overlap Alteration Bypass ---

def test_low_overlap_bypass():
    """
    Verify that highly altered text in the active field (<=50% overlap) raises ValueError
    when the exact copy is placed in a dummy field.
    """
    original_text = "we will help you achieve your goals and find happiness"
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content=original_text
    )
    
    # Active field contains highly altered version (30% overlap)
    altered_text = "we offer help and sell products to make money"
    
    payload = {
        "dummy": original_text, # exact copy
        "active": altered_text  # low overlap alteration
    }
    adapter = DirectPayloadAdapter(payload=payload)
    
    with pytest.raises(ValueError) as exc_info:
        route(strategy, adapter)
    assert "Integrity Violation" in str(exc_info.value)


# --- 5. Substring Addition / Hype Prepend/Append Bypass ---

def test_substring_addition_bypass():
    """
    Verify that prepending/appending hype to the copy in the active field raises ValueError.
    """
    original_text = "This is a strictly validated psychological intervention."
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content=original_text
    )
    
    payload = {
        "active": f"[Original Copy] {original_text} BUY NOW!"
    }
    adapter = DirectPayloadAdapter(payload=payload)
    
    with pytest.raises(ValueError) as exc_info:
        route(strategy, adapter)
    assert "Integrity Violation" in str(exc_info.value)
    assert "substring addition" in str(exc_info.value).lower()


# --- 6. Split Payload Bypass ---

def test_split_payload_bypass():
    """
    Verify that splitting the copy across multiple fields raises ValueError,
    even if the exact copy is in a dummy field.
    """
    original_text = "This is a strictly validated psychological intervention."
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content=original_text
    )
    
    payload = {
        "dummy": original_text,
        "part1": "This is a strictly",
        "part2": " validated psychological intervention."
    }
    adapter = DirectPayloadAdapter(payload=payload)
    
    with pytest.raises(ValueError) as exc_info:
        route(strategy, adapter)
    assert "Integrity Violation" in str(exc_info.value)


# --- 7. Punctuation-Only Copy Support and Integrity Checks ---

def test_punctuation_only_copy_and_alteration():
    """
    Verify that punctuation-only copy does not crash on creation/routing,
    but still raises ValueError if altered.
    """
    # 1. Happy path: punctuation-only copy routed verbatim
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content="..."
    )
    adapter = DirectPayloadAdapter(payload={"text": "..."})
    res = route(strategy, adapter)
    assert "..." in res

    # 2. Alteration path: punctuation-only copy altered/augmented
    adapter_altered = DirectPayloadAdapter(payload={"text": "... BUY NOW!"})
    with pytest.raises(ValueError) as exc_info:
        route(strategy, adapter_altered)
    assert "Integrity Violation" in str(exc_info.value)


# --- 8. Whitespace and Formatting Strictness ---

def test_whitespace_variants():
    """
    Verify that whitespace-only variations (tabs, newlines) do NOT raise ValueError
    as long as characters and spelling match, but actual additions do.
    """
    original_text = "hello world intervention"
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content=original_text
    )
    
    # Payload has tabs and newlines instead of spaces
    payload = {"text": "hello\tworld\nintervention"}
    adapter = DirectPayloadAdapter(payload=payload)
    
    # Should route successfully since it's just spacing formatting
    res = route(strategy, adapter)
    assert "hello\\tworld\\nintervention" in res


# --- 9. DoS/Performance Stress Testing ---

def test_long_string_performance():
    """Verify the router handles very long strings without crashing or extreme slow-down."""
    long_word = "word"
    long_content = " ".join([long_word] * 10000)
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(funnel_stage=FunnelStage.AWARENESS),
        content=long_content
    )
    payload = {"text": long_content}
    adapter = DirectPayloadAdapter(payload=payload)
    
    import time
    start_time = time.time()
    json_payload = route(strategy, adapter)
    elapsed = time.time() - start_time
    
    assert json_payload is not None
    assert elapsed < 0.5
