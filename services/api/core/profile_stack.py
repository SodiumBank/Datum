"""Standards Profile Stack - layered compliance profile system (Sprint 4).

Implements BASE → DOMAIN → CUSTOMER_OVERRIDE profile hierarchy with inheritance and conflict resolution.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from services.api.core.schema_validation import validate_schema

ROOT = Path(__file__).resolve().parents[4]
PROFILES_DIR = ROOT / "standards_profiles"


def load_profile(profile_id: str) -> Dict[str, Any]:
    """
    Load a standards profile by ID.
    
    Args:
        profile_id: Profile identifier
    
    Returns:
        Profile object
    
    Raises:
        ValueError: If profile not found or invalid
    """
    profile_path = PROFILES_DIR / f"{profile_id}.json"
    
    if not profile_path.exists():
        raise ValueError(f"Profile not found: {profile_id}")
    
    with open(profile_path, encoding="utf-8") as f:
        profile = json.load(f)
    
    # Validate schema
    try:
        validate_schema(profile, "standards_profile.schema.json")
    except Exception as e:
        raise ValueError(f"Invalid profile schema: {e}") from e
    
    return profile


def resolve_profile_stack(profile_ids: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Resolve a profile stack with inheritance and conflict detection.
    
    Args:
        profile_ids: List of profile IDs in stack order
    
    Returns:
        Tuple of (resolved_profiles, errors)
    
    Profile stack is resolved in order:
    1. BASE profiles (no parents)
    2. DOMAIN profiles (inherit from BASE)
    3. CUSTOMER_OVERRIDE profiles (inherit from DOMAIN)
    """
    resolved: List[Dict[str, Any]] = []
    errors: List[str] = []
    loaded_profiles: Dict[str, Dict[str, Any]] = {}
    
    # Load all profiles
    for profile_id in profile_ids:
        try:
            profile = load_profile(profile_id)
            loaded_profiles[profile_id] = profile
        except ValueError as e:
            errors.append(f"Failed to load profile {profile_id}: {e}")
            continue
    
    # Group by type
    base_profiles: List[Dict[str, Any]] = []
    domain_profiles: List[Dict[str, Any]] = []
    customer_profiles: List[Dict[str, Any]] = []
    
    for profile_id, profile in loaded_profiles.items():
        profile_type = profile.get("profile_type")
        if profile_type == "BASE":
            base_profiles.append(profile)
        elif profile_type == "DOMAIN":
            domain_profiles.append(profile)
        elif profile_type == "CUSTOMER_OVERRIDE":
            customer_profiles.append(profile)
        else:
            errors.append(f"Invalid profile_type for {profile_id}: {profile_type}")
    
    # Validate inheritance
    for profile in domain_profiles:
        parents = profile.get("parent_profiles", [])
        if not parents:
            errors.append(f"DOMAIN profile {profile['profile_id']} must have parent_profiles")
        for parent_id in parents:
            parent_profile = loaded_profiles.get(parent_id)
            if not parent_profile:
                errors.append(f"DOMAIN profile {profile['profile_id']} references unknown parent: {parent_id}")
            elif parent_profile.get("profile_type") != "BASE":
                errors.append(f"DOMAIN profile {profile['profile_id']} can only inherit from BASE, not {parent_id}")
    
    for profile in customer_profiles:
        parents = profile.get("parent_profiles", [])
        if not parents:
            errors.append(f"CUSTOMER_OVERRIDE profile {profile['profile_id']} must have parent_profiles")
        for parent_id in parents:
            parent_profile = loaded_profiles.get(parent_id)
            if not parent_profile:
                errors.append(f"CUSTOMER_OVERRIDE profile {profile['profile_id']} references unknown parent: {parent_id}")
            elif parent_profile.get("profile_type") != "DOMAIN":
                errors.append(f"CUSTOMER_OVERRIDE profile {profile['profile_id']} can only inherit from DOMAIN, not {parent_id}")
    
    # Check for circular dependencies
    # (Simplified: just check direct parent references)
    for profile_id, profile in loaded_profiles.items():
        parents = profile.get("parent_profiles", [])
        for parent_id in parents:
            parent_profile = loaded_profiles.get(parent_id)
            if parent_profile and profile_id in parent_profile.get("parent_profiles", []):
                errors.append(f"Circular dependency detected: {profile_id} <-> {parent_id}")
    
    if errors:
        return ([], errors)
    
    # Build resolved stack (BASE → DOMAIN → CUSTOMER_OVERRIDE)
    resolved.extend(base_profiles)
    resolved.extend(domain_profiles)
    resolved.extend(customer_profiles)
    
    return (resolved, [])


def apply_profile_inheritance(profile: Dict[str, Any], parent_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply inheritance from parent profiles to child profile.
    
    Args:
        profile: Child profile
        parent_profiles: Parent profiles (in order of precedence)
    
    Returns:
        Inherited profile with parent rules merged
    """
    inherited = profile.copy()
    
    # Determine override mode
    inheritance_rules = profile.get("inheritance_rules", {})
    override_mode = inheritance_rules.get("override_mode", "ADDITIVE")
    conflict_resolution = inheritance_rules.get("conflict_resolution", "ERROR")
    
    # Merge parent standards_packs (additive by default)
    all_packs = set(inherited.get("standards_packs", []))
    for parent in parent_profiles:
        parent_packs = parent.get("standards_packs", [])
        all_packs.update(parent_packs)
    
    inherited["standards_packs"] = sorted(list(all_packs))
    
    # Merge source_standards (additive)
    all_standards = {s["standard_id"]: s for s in inherited.get("source_standards", [])}
    for parent in parent_profiles:
        for std in parent.get("source_standards", []):
            std_id = std["standard_id"]
            if std_id not in all_standards:
                all_standards[std_id] = std
            elif conflict_resolution == "CHILD_WINS":
                # Child overrides parent
                all_standards[std_id] = std
            elif conflict_resolution == "ERROR":
                # Check if clauses conflict
                existing = all_standards[std_id]
                if existing.get("clause") != std.get("clause"):
                    raise ValueError(
                        f"Standard {std_id} clause conflict: "
                        f"parent has {existing.get('clause')}, child has {std.get('clause')}"
                    )
    
    inherited["source_standards"] = list(all_standards.values())
    
    return inherited


def tag_decision_with_profile(
    decision: Dict[str, Any],
    profile_id: str,
    profile_type: str,
    layer: int,
    clause_reference: str | None = None,
) -> Dict[str, Any]:
    """
    Tag an SOE decision with profile source information.
    
    Args:
        decision: SOE decision object
        profile_id: Profile ID that generated this decision
        profile_type: Profile type (BASE/DOMAIN/CUSTOMER_OVERRIDE)
        layer: Profile layer in stack (0=BASE, 1=DOMAIN, 2=CUSTOMER_OVERRIDE)
        clause_reference: Clause reference from source standard
    
    Returns:
        Decision with profile metadata added
    """
    tagged = decision.copy()
    
    if "profile_source" not in tagged:
        tagged["profile_source"] = profile_id
    if "profile_type" not in tagged:
        tagged["profile_type"] = profile_type
    if "profile_layer" not in tagged:
        tagged["profile_layer"] = layer
    if clause_reference:
        tagged["clause_reference"] = clause_reference
    
    return tagged
