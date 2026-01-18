import json
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS = ROOT / "schemas"


def _load_schema_store() -> dict[str, dict]:
    store: dict[str, dict] = {}
    for path in SCHEMAS.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        schema_id = data.get("$id")
        if schema_id:
            store[schema_id] = data
        store[path.as_uri()] = data
    return store


_SCHEMA_STORE = _load_schema_store()


def validate_schema(instance: dict, schema_filename: str) -> None:
    schema_path = SCHEMAS / schema_filename
    schema = _SCHEMA_STORE.get(schema_path.as_uri())
    if not schema:
        raise ValueError(f"Schema not found: {schema_filename}")
    resolver = RefResolver.from_schema(schema, store=_SCHEMA_STORE)
    Draft202012Validator(schema, resolver=resolver).validate(instance)
