import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS = ROOT / "schemas"

def main() -> None:
    # Smoke-validate that every schema file is valid Draft2020-12 JSON schema.
    for p in SCHEMAS.glob("*.json"):
        data = json.loads(p.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(data)
    print(f"OK: validated {len(list(SCHEMAS.glob('*.json')))} schemas")

if __name__ == "__main__":
    main()
