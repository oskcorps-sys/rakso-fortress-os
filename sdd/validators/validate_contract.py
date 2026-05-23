"""Validator for CONTRACT.yaml artifacts."""

import yaml
from pathlib import Path
from typing import Dict, Any, Union
from pydantic import ValidationError
from sdd.schemas.contract import ContractSchema
from sdd.schemas.base import ValidationResult, ErrorItem


def validate_contract(
    artifact_path: Union[str, Path],
    schema_name: str = "contract"
) -> ValidationResult:
    """
    Validate a CONTRACT.yaml artifact against ContractSchema.

    Args:
        artifact_path: Path to YAML file or dict
        schema_name: Schema name (should be 'contract')

    Returns:
        ValidationResult with valid status and errors/warnings
    """
    try:
        # Load YAML
        if isinstance(artifact_path, (str, Path)):
            with open(artifact_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        else:
            data = artifact_path

        # Validate against schema
        try:
            ContractSchema.model_validate(data)
            return ValidationResult(
                valid=True,
                schema_name=schema_name,
                errors=[],
                warnings=[]
            )
        except ValidationError as e:
            errors = [
                ErrorItem(
                    field=str(err["loc"]),
                    message=err["msg"],
                    value=err.get("input")
                )
                for err in e.errors()
            ]
            return ValidationResult(
                valid=False,
                schema_name=schema_name,
                errors=errors,
                warnings=[]
            )

    except FileNotFoundError as e:
        return ValidationResult(
            valid=False,
            schema_name=schema_name,
            errors=[
                ErrorItem(
                    field="file",
                    message=f"File not found: {artifact_path}",
                    value=None
                )
            ],
            warnings=[]
        )
    except yaml.YAMLError as e:
        return ValidationResult(
            valid=False,
            schema_name=schema_name,
            errors=[
                ErrorItem(
                    field="yaml",
                    message=f"Invalid YAML: {str(e)}",
                    value=None
                )
            ],
            warnings=[]
        )
    except Exception as e:
        return ValidationResult(
            valid=False,
            schema_name=schema_name,
            errors=[
                ErrorItem(
                    field="unknown",
                    message=f"Unexpected error: {str(e)}",
                    value=None
                )
            ],
            warnings=[]
        )
