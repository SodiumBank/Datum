"""Profile Versioning and History (Sprint 5).

Track versions of standards profiles with full audit history.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from services.api.core.profile_stack import load_profile
from services.api.core.schema_validation import validate_schema

ROOT = Path(__file__).resolve().parents[4]
PROFILES_DIR = ROOT / "standards_profiles"


def create_profile_version(
    profile_id: str,
    new_version: str,
    parent_version: str | None = None,
) -> Dict[str, Any]:
    """
    Create a new version of a profile.
    
    Profile versions are stored as: {profile_id}.v{version}.json
    
    Args:
        profile_id: Base profile ID
        new_version: New version string (semver: X.Y.Z)
        parent_version: Parent version this is derived from
    
    Returns:
        New profile version with version metadata
    """
    # Load current profile
    profile = load_profile(profile_id)
    
    # Add version metadata
    if "metadata" not in profile:
        profile["metadata"] = {}
    
    profile["version"] = new_version
    profile["metadata"]["parent_version"] = parent_version or profile.get("version")
    profile["metadata"]["version_created_at"] = datetime.now(timezone.utc).isoformat()
    
    # Validate
    validate_schema(profile, "standards_profile.schema.json")
    
    # Save as versioned file
    versioned_path = PROFILES_DIR / f"{profile_id}.v{new_version}.json"
    with open(versioned_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    
    return profile


def load_profile_version(profile_id: str, version: str | None = None) -> Dict[str, Any]:
    """
    Load a specific version of a profile.
    
    Args:
        profile_id: Base profile ID
        version: Version string (if None, loads latest)
    
    Returns:
        Profile version
    """
    if version:
        versioned_path = PROFILES_DIR / f"{profile_id}.v{version}.json"
        if versioned_path.exists():
            with open(versioned_path, encoding="utf-8") as f:
                return json.load(f)
    
    # Fall back to base profile
    return load_profile(profile_id)


def list_profile_versions(profile_id: str) -> List[Dict[str, Any]]:
    """
    List all versions of a profile.
    
    Returns:
        List of version metadata
    """
    versions: List[Dict[str, Any]] = []
    
    # Load base profile
    try:
        base_profile = load_profile(profile_id)
        versions.append({
            "version": base_profile.get("version", "1.0.0"),
            "is_base": True,
            "state": base_profile.get("metadata", {}).get("state", "draft"),
        })
    except ValueError:
        pass
    
    # Find versioned files
    pattern = f"{profile_id}.v*.json"
    for versioned_path in PROFILES_DIR.glob(pattern):
        try:
            with open(versioned_path, encoding="utf-8") as f:
                profile = json.load(f)
                versions.append({
                    "version": profile.get("version"),
                    "is_base": False,
                    "state": profile.get("metadata", {}).get("state", "draft"),
                    "parent_version": profile.get("metadata", {}).get("parent_version"),
                })
        except Exception:
            continue
    
    # Sort by version (semver)
    versions.sort(key=lambda v: _parse_semver(v.get("version", "0.0.0")))
    
    return versions


def _parse_semver(version: str) -> Tuple[int, int, int]:
    """Parse semver string to tuple for sorting."""
    parts = version.split(".")
    return (
        int(parts[0]) if len(parts) > 0 else 0,
        int(parts[1]) if len(parts) > 1 else 0,
        int(parts[2]) if len(parts) > 2 else 0,
    )


def compare_profile_versions(
    profile_id: str,
    version1: str,
    version2: str,
) -> Dict[str, Any]:
    """
    Compare two profile versions and generate diff.
    
    Args:
        profile_id: Base profile ID
        version1: First version
        version2: Second version
    
    Returns:
        Diff object showing changes
    """
    profile1 = load_profile_version(profile_id, version1)
    profile2 = load_profile_version(profile_id, version2)
    
    diff: Dict[str, Any] = {
        "profile_id": profile_id,
        "version1": version1,
        "version2": version2,
        "changes": [],
    }
    
    # Compare basic fields
    for field in ["profile_type", "name"]:
        if profile1.get(field) != profile2.get(field):
            diff["changes"].append({
                "field": field,
                "old_value": profile1.get(field),
                "new_value": profile2.get(field),
                "change_type": "modified",
            })
    
    # Compare version
    if profile1.get("version") != profile2.get("version"):
        diff["changes"].append({
            "field": "version",
            "old_value": profile1.get("version"),
            "new_value": profile2.get("version"),
            "change_type": "modified",
        })
    
    # Compare standards_packs
    packs1 = set(profile1.get("standards_packs", []))
    packs2 = set(profile2.get("standards_packs", []))
    
    added_packs = packs2 - packs1
    removed_packs = packs1 - packs2
    
    for pack in added_packs:
        diff["changes"].append({
            "field": "standards_packs",
            "change_type": "added",
            "value": pack,
        })
    
    for pack in removed_packs:
        diff["changes"].append({
            "field": "standards_packs",
            "change_type": "removed",
            "value": pack,
        })
    
    # Compare source_standards
    standards1 = {s.get("standard_id"): s for s in profile1.get("source_standards", [])}
    standards2 = {s.get("standard_id"): s for s in profile2.get("source_standards", [])}
    
    for std_id in set(list(standards1.keys()) + list(standards2.keys())):
        if std_id not in standards1:
            diff["changes"].append({
                "field": "source_standards",
                "change_type": "added",
                "value": standards2[std_id],
            })
        elif std_id not in standards2:
            diff["changes"].append({
                "field": "source_standards",
                "change_type": "removed",
                "value": standards1[std_id],
            })
        elif standards1[std_id] != standards2[std_id]:
            diff["changes"].append({
                "field": "source_standards",
                "change_type": "modified",
                "old_value": standards1[std_id],
                "new_value": standards2[std_id],
            })
    
    return diff
