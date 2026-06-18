import pytest
from sdd.schemas.rakso_core import OutputStatus, StrategyOutput, NeurofunnelMap, FunnelStage
from sdd.skills.rakso_engines.the_bridge import TheBridgeEngine

def test_bridge_blocks_hype():
    engine = TheBridgeEngine()
    
    # Mock output containing forbidden terms
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(
            funnel_stage=FunnelStage.AWARENESS,
            core_emotion="Confusion",
            cognitive_bias="Confirmation",
            psychological_goal="Break certainty",
            next_expected_action="Read"
        ),
        content="This system will guarantee you achieve your dreams and fix your life!"
    )
    
    decision = engine.evaluate_output(strategy)
    
    assert decision.status == OutputStatus.BLOCKED
    assert not decision.is_executable()
    assert len(decision.violations_detected) >= 2

def test_bridge_northstar_context_override():
    engine = TheBridgeEngine()
    
    strategy = StrategyOutput(
        neurofunnel_map=NeurofunnelMap(
            funnel_stage=FunnelStage.AWARENESS,
            core_emotion="Suspicion",
            cognitive_bias="Confirmation",
            psychological_goal="Expose risk",
            next_expected_action="Read"
        ),
        content="This analysis provides a clear transformation for your growth journey."
    )
    
    decision = engine.evaluate_output(strategy, active_context="NORTHSTAR HUB")
    
    # Growth, journey, transformation are forbidden in Northstar
    assert decision.status == OutputStatus.BLOCKED
    assert "NORTHSTAR HUB" in decision.violations_detected[0]
