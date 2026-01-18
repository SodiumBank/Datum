"""Profile Bundles - Group profiles by program/customer/contract (Sprint 5)."""

import json
from pathlib import Path
from typing import Any, Dict, List

from services.api.core.schema_validation import validate_schema

ROOT = Path(__file__).resolve().parents[4]
BUNDLES_DIR = ROOT / "standards_profiles" / "bundles"
BUNDLES_DIR.mkdir(parents=True, exist_ok=True)


def save_profile_bundle(bundle: Dict[str, Any]) -> None:
    """Save a profile bundle."""
    bundle_id = bundle.get("bundle_id")
    if not bundle_id:
        raise ValueError("bundle_id is required")
    
    # Validate schema
    validate_schema(bundle, "profile_bundle.schema.json")
    
    # Save
    bundle_path = BUNDLES_DIR / f"{bundle_id}.json"
    with open(bundle_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False)


def load_profile_bundle(bundle_id: str) -> Dict[str, Any]:
    """Load a profile bundle."""
    bundle_path = BUNDLES_DIR / f"{bundle_id}.json"
    
    if not bundle_path.exists():
        raise ValueError(f"Bundle not found: {bundle_id}")
    
    with open(bundle_path, encoding="utf-8") as f:
        bundle = json.load(f)
    
    validate_schema(bundle, "profile_bundle.schema.json")
    return bundle


def list_profile_bundles() -> List[Dict[str, Any]]:
    """List all profile bundles."""
    bundles: List[Dict[str, Any]] = []
    
    for bundle_path in BUNDLES_DIR.glob("*.json"):
        try:
            with open(bundle_path, encoding="utf-8") as f:
                bundle = json.load(f)
                bundles.append({
                    "bundle_id": bundle.get("bundle_id"),
                    "name": bundle.get("name"),
                    "profile_count": len(bundle.get("profile_ids", [])),
                    "program_id": bundle.get("program_id"),
                    "customer_id": bundle.get("customer_id"),
                })
        except Exception:
            continue
    
    return bundles


def resolve_bundle_profiles(bundle_id: str) -> List[str]:
    """
    Resolve bundle to list of profile IDs.
    
    Args:
        bundle_id: Bundle identifier
    
    Returns:
        List of profile IDs in bundle
    """
    bundle = load_profile_bundle(bundle_id)
    return bundle.get("profile_ids", [])
