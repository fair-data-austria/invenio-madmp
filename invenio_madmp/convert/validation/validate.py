"""Functions for validating maDMP JSONs against the RDA maDMP JSON Schema."""

import json
import os.path
from typing import List

import jsonschema
import jsonschema.exceptions


def get_schema(schema_file_name: str = None) -> dict:
    """Load the maDMP jsonschema provided in the module."""
    module_dir = os.path.split(__file__)[0]
    schema_file_name = schema_file_name or "maDMP-schema-1.0.json"
    file_path = os.path.join(module_dir, "schema", schema_file_name)
    schema = None

    with open(file_path, "r") as json_file:
        schema = json.load(json_file)

    return schema


def get_errors(dmp_json) -> List[jsonschema.exceptions.ValidationError]:
    """Get a list of all validation errors in the specified maDMP json."""
    validator = jsonschema.Draft7Validator(get_schema())
    errors = list(validator.iter_errors(dmp_json))
    return errors


def get_error_messages(dmp_json) -> List[str]:
    """Get a list of all validation error messages in the specified maDMP json."""
    return [err.message for err in get_errors(dmp_json)]


def validate(dmp_json) -> bool:
    """Check if the specified maDMP json follows the RDA maDMP JSON Schema."""
    validator = jsonschema.Draft7Validator(get_schema())

    try:
        validator.validate(dmp_json)
    except jsonschema.exceptions.ValidationError:
        return False

    return True
