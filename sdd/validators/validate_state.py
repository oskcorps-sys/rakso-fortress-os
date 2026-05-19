"""Validator for STATE_SNAPSHOT.yaml artifacts."""

import yaml
from pathlib import Path
from typing import Union
from pydantic import ValidationError
from sdd.schemas.state import StateSnapshotSchema
from sdd.schemas.base import ValidationResult, ErrorItem


def validate_state(
    artifact_path: Union[str, Path],
    schema_name: str = "state"
) -> ValidationResult:
    """
    Validate a STATE_SNAPSHOT.yaml artifact against StateSnapshotSchema.

    Args:
        artifact_path: Path to YAML file or dict
        schema_name: Schema name (should be 'state')

    Returns:
        ValidationResult with valid status and errors/warnings
    """
    try:
        # Load YAML
        if isinstance(artifact_path, (str, Path)):
            with open(artifact_path, 'r') as f:
                data = yaml.safe_load(f)
        else:
            data = artifact_path

        # Validate against schema
        try:
            StateSnapshotSchema.model_validate(data)
            return ValidationResult(
                valid=True,
                schema=schema_name,
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
                schema=schema_name,
                errors=errors,
                warnings=[]
            )

    except FileNotFoundError as e:
        return ValidationResult(
            valid=False,
            schema=schema_name,
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
            schema=schema_name,
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
            schema=schema_name,
            errors=[
                ErrorItem(
                    field="unknown",
                    message=f"Unexpected error: {str(e)}",
                    value=None
                )
            ],
            warnings=[]
        )
