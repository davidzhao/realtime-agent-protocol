"""Schema-validation layer of the conformance suite (spec §4–§8).

Every fixture under ``fixtures/valid/<schema>/`` MUST validate against
``schemas/v0.1/<schema>.schema.json``; every fixture under ``fixtures/invalid/<schema>/``
MUST fail it. Fixtures are discovered by directory, so new cases need no test changes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_registry import REPO_ROOT, validator_for

FIXTURES = REPO_ROOT / "fixtures"


def _cases(kind: str):
    base = FIXTURES / kind
    for path in sorted(base.glob("*/*.json")):
        schema_name = path.parent.name
        yield pytest.param(schema_name, path, id=f"{kind}/{schema_name}/{path.name}")


@pytest.mark.parametrize("schema_name,path", list(_cases("valid")))
def test_valid_fixture_passes(schema_name: str, path: Path) -> None:
    validator = validator_for(schema_name)
    instance = json.loads(path.read_text())
    errors = sorted(validator.iter_errors(instance), key=str)
    assert not errors, f"{path} should validate against {schema_name}: {errors}"


@pytest.mark.parametrize("schema_name,path", list(_cases("invalid")))
def test_invalid_fixture_fails(schema_name: str, path: Path) -> None:
    validator = validator_for(schema_name)
    instance = json.loads(path.read_text())
    assert not validator.is_valid(instance), (
        f"{path} should FAIL validation against {schema_name} but passed"
    )


def test_every_schema_has_valid_and_invalid_fixtures() -> None:
    """Guards against a schema drifting out of fixture coverage."""
    schema_dir = REPO_ROOT / "schemas" / "v0.1"
    schemas = {
        p.name.removesuffix(".schema.json")
        for p in schema_dir.glob("*.json")
    } - {"common"}  # common holds only $defs
    valid = {p.name for p in (FIXTURES / "valid").glob("*") if p.is_dir()}
    invalid = {p.name for p in (FIXTURES / "invalid").glob("*") if p.is_dir()}
    missing_valid = schemas - valid
    missing_invalid = schemas - invalid
    assert not missing_valid, f"schemas without a valid fixture: {sorted(missing_valid)}"
    assert not missing_invalid, f"schemas without an invalid fixture: {sorted(missing_invalid)}"
