from typing import Dict, Any
from sdd.schemas.rakso_core import FunnelStage, NeurofunnelMap

class NeurofunnelEngine:
    """
    LAYER 4: NEUROFUNNEL ENGINE
    Function: Define the neurological purpose of every piece of content.
    """
    
    STAGE_DEFINITIONS = {
        FunnelStage.AWARENESS: {
            "state": "Something feels wrong.",
            "goal": "Break false certainty.",
            "emotions": ["Confusion", "Suspicion", "Cognitive discomfort"],
            "expected_action": ["Read", "Save", "Reflect silently"]
        },
        FunnelStage.DESTABILIZATION: {
            "state": "I may be operating incorrectly.",
            "goal": "Expose hidden mistake.",
            "emotions": ["Fear", "Shame", "Urgency"],
            "expected_action": ["Re-read", "Investigate", "Comment"]
        },
        FunnelStage.VALIDATION: {
            "state": "This explains my situation.",
            "goal": "Validate experience.",
            "emotions": ["Relief", "Rational trust", "Clarity"],
            "expected_action": ["Follow", "Share privately", "Consume more"]
        },
        FunnelStage.PRE_DECISION: {
            "state": "I should stop improvising.",
            "goal": "Prevent impulsive action.",
            "emotions": ["Prudence", "Control", "Self-protection"],
            "expected_action": ["Visit profile", "Enter diagnosis", "Read long-form content"]
        },
        FunnelStage.BRIDGE: {
            "state": "I need to validate before acting.",
            "goal": "Connect problem -> diagnostic mechanism",
            "emotions": ["Determination"],
            "expected_action": ["Risk Detector", "Diagnostic tool", "Protocol validation"]
        }
    }

    def generate_map(self, stage: FunnelStage) -> NeurofunnelMap:
        """Generates a strict Neurofunnel map for the strategy engine to follow."""
        definition = self.STAGE_DEFINITIONS[stage]
        return NeurofunnelMap(
            funnel_stage=stage,
            core_emotion=definition["emotions"][0],
            cognitive_bias="Confirmation Bias Interruption", # Default for now
            psychological_goal=definition["goal"],
            next_expected_action=definition["expected_action"][0]
        )
