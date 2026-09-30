"""Build a jsonschema validator registry from the local schema files.

Each schema's ``$id`` is its published URL under the extension-URI namespace, and
cross-schema ``$ref``s are relative (e.g. ``common.schema.json#/$defs/...``). Because
RFC 3986 resolves a relative reference against the referring schema's ``$id`` base, a
registry keyed by ``$id`` resolves the local set without any network access.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "schemas" / "v0.1"


def _load_registry() -> Registry:
    registry = Registry()
    for path in sorted(SCHEMA_DIR.glob("*.json")):
        contents = json.loads(path.read_text())
        resource = Resource.from_contents(contents)
        registry = resource @ registry  # register under the schema's own $id
    return registry


_REGISTRY = _load_registry()


def validator_for(schema_name: str) -> Draft202012Validator:
    """Return a validator for ``schemas/v0.1/<schema_name>.schema.json``."""
    uri = (
        "https://schemas.salesforce.com/a2a/ext/realtime-agent/v0.1/"
        f"{schema_name}.schema.json"
    )
    schema = _REGISTRY.get_or_retrieve(uri).value.contents
    return Draft202012Validator(schema, registry=_REGISTRY)
