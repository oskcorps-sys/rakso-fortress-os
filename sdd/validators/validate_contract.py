"""
Validate CONTRACT.yaml against schema.

Implemented in: Phase 1
Used by: Claude Code (auditor) during each phase audit
"""

from pathlib import Path
from typing import Any, Dict
import yaml


def validate_contract(contract_path: str | Path) -> Dict[str, Any]:
    """
    Validate CONTRACT.yaml exists and has required structure.
    
    Phase 1: Basic structure validation
    Phase 3+: Full schema validation via pydantic
    
    Args:
        contract_path: Path to CONTRACT.yaml
        
    Returns:
        {"valid": bool, "errors": [str], "warnings": [str]}
    """
    contract_path = Path(contract_path)
    
    if not contract_path.exists():
        return {
            "valid": False,
            "errors": [f"CONTRACT.yaml not found at {contract_path}"],
            "warnings": [],
        }
    
    try:
        with open(contract_path) as f:
            contract = yaml.safe_load(f)
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Failed to parse YAML: {e}"],
            "warnings": [],
        }
    
    # Phase 1: Check required fields
    required_fields = ["phase", "specification", "inputs", "outputs"]
    missing = [f for f in required_fields if f not in contract]
    
    if missing:
        return {
            "valid": False,
            "errors": [f"Missing required fields: {', '.join(missing)}"],
            "warnings": [],
        }
    
    return {
        "valid": True,
        "errors": [],
        "warnings": [],
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python validate_contract.py <contract_path>")
        sys.exit(1)
    
    result = validate_contract(sys.argv[1])
    print(result)
    sys.exit(0 if result["valid"] else 1)
