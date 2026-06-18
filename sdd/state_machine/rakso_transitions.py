from enum import Enum

class RaksoSystemState(str, Enum):
    # Hierarchy Layer 1
    CONTEXT_DECLARATION = "CONTEXT_DECLARATION"
    # Hierarchy Layer 2
    CONTEXT_OVERRIDE = "CONTEXT_OVERRIDE"
    # Hierarchy Layer 3
    RAKSO_CORE_STRATEGY = "RAKSO_CORE_STRATEGY"
    # Hierarchy Layer 4
    NEUROFUNNEL_MAP = "NEUROFUNNEL_MAP"
    # Hierarchy Layer 5
    THE_BRIDGE_VALIDATION = "THE_BRIDGE_VALIDATION"
    # Hierarchy Layer 6
    MODULE_C_CONSTRAINTS = "MODULE_C_CONSTRAINTS"
    # Hierarchy Layer 7
    VALUE_LADDER_ENGINE = "VALUE_LADDER_ENGINE"
    # Hierarchy Layer 8
    DECISION_OUTPUT = "DECISION_OUTPUT"
    # Hierarchy Layer 9
    NEURO_ROUTER = "NEURO_ROUTER"
    # Hierarchy Layer 10
    TRAFFICKER_EXECUTION = "TRAFFICKER_EXECUTION"
    # Hierarchy Layer 11
    FEEDBACK_LOOP = "FEEDBACK_LOOP"

class RaksoStateMachine:
    """
    Manages the strict transition through the 12 System Authority Layers.
    ANY FAILED CONSTRAINT -> HARD STOP (Return to CONTEXT_DECLARATION or THE_BRIDGE).
    """
    
    def __init__(self):
        self.current_state = RaksoSystemState.CONTEXT_DECLARATION
        
    def transition(self, next_state: RaksoSystemState, validation_passed: bool = True):
        """
        Transition logic. If validation fails, it triggers a HARD STOP.
        """
        if not validation_passed:
            # Rule: ANY FAILED CONSTRAINT -> HARD STOP
            # If issue detected by Trafficker -> RETURN TO BRIDGE
            if self.current_state == RaksoSystemState.TRAFFICKER_EXECUTION:
                self.current_state = RaksoSystemState.THE_BRIDGE_VALIDATION
            else:
                self.current_state = RaksoSystemState.CONTEXT_DECLARATION
            return False
            
        self.current_state = next_state
        return True
