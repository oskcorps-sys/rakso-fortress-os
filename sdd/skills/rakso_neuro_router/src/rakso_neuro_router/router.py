import json
from typing import Any, Union, Dict
from rakso_neuro_router.models import StrategyOutput
from rakso_neuro_router.adapters.base import TargetAdapter
from rakso_neuro_router.validation import validate_no_alteration

def route(strategy_output: Union[StrategyOutput, Dict[str, Any]], adapter_instance: TargetAdapter) -> str:
    """
    Route a strategic output through an adapter instance.
    Validates models, enforces integrity constraint checks, and returns a JSON payload string.
    """
    if not isinstance(strategy_output, StrategyOutput):
        strategy_output = StrategyOutput.model_validate(strategy_output)

    if not isinstance(adapter_instance, TargetAdapter):
        raise TypeError("adapter_instance must be an instance of a TargetAdapter subclass")

    original_text = strategy_output.content
    payload = adapter_instance.transform(strategy_output)
    
    # Run strict no-alteration verification
    validate_no_alteration(
        original_text,
        payload,
        active_paths=adapter_instance.active_copy_paths,
        metadata_paths=adapter_instance.metadata_paths
    )

    return json.dumps(payload, indent=2)
