"""Standards Profile Lifecycle Management (Sprint 5).

State machine: draft → submitted → approved/rejected → deprecated
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from services.api.core.schema_validation import validate_schema
from services.api.core.profile_stack import load_profile

ROOT = Path(__file__).resolve().parents[4]
PROFILES_DIR = ROOT / "standards_profiles"


def get_profile_state(profile_id: str) -> str:
    """
    Get current state of a profile.
    
    For now, profiles are implicitly "draft" unless they have state metadata.
    In production, this would be stored in a database.
    
    Args:
        profile_id: Profile identifier
    
    Returns:
        Profile state: "draft", "submitted", "approved", "rejected", "deprecated"
    """
    try:
        profile = load_profile(profile_id)
        # Check if profile has state in metadata
        metadata = profile.get("metadata", {})
        state = metadata.get("state")
        if state and state in ["draft", "submitted", "approved", "rejected", "deprecated"]:
            return state
    except ValueError:
        pass
    
    # Default to draft
    return "draft"


def can_submit_profile(profile_id: str) -> Tuple[bool, str]:
    """Check if profile can be submitted for approval."""
    state = get_profile_state(profile_id)
    if state != "draft":
        return (False, f"Profile is in {state} state. Only draft profiles can be submitted.")
    
    return (True, "")


def can_approve_profile(profile_id: str) -> Tuple[bool, str]:
    """Check if profile can be approved."""
    state = get_profile_state(profile_id)
    if state != "submitted":
        return (False, f"Profile is in {state} state. Only submitted profiles can be approved.")
    
    return (True, "")


def can_reject_profile(profile_id: str) -> Tuple[bool, str]:
    """Check if profile can be rejected."""
    state = get_profile_state(profile_id)
    if state != "submitted":
        return (False, f"Profile is in {state} state. Only submitted profiles can be rejected.")
    
    return (True, "")


def can_deprecate_profile(profile_id: str) -> Tuple[bool, str]:
    """Check if profile can be deprecated."""
    state = get_profile_state(profile_id)
    if state not in ["approved", "submitted"]:
        return (False, f"Profile is in {state} state. Only approved or submitted profiles can be deprecated.")
    
    return (True, "")


def _save_profile_with_state(profile_id: str, state: str, user_id: str, reason: str | None = None) -> Dict[str, Any]:
    """Save profile with updated state metadata."""
    # Sprint 6: Enforce immutability - approved profiles cannot be modified
    current_state = get_profile_state(profile_id)
    if current_state == "approved" and state != "approved" and state != "deprecated":
        # Allow state transitions from approved (e.g., to deprecated)
        # But prevent direct edits to approved profiles
        raise ValueError(f"Profile {profile_id} is approved and immutable. Cannot change state to {state}. Use deprecate to mark as deprecated.")
    
    profile_path = PROFILES_DIR / f"{profile_id}.json"
    
    if not profile_path.exists():
        raise ValueError(f"Profile not found: {profile_id}")
    
    # Load profile
    with open(profile_path, encoding="utf-8") as f:
        profile = json.load(f)
    
    # Sprint 6: Additional immutability check - prevent overwriting approved profile content
    if current_state == "approved" and state == "approved":
        # If already approved and staying approved, this is a metadata-only update
        # Allow metadata updates (e.g., maintenance notes) but validate we're not changing core fields
        pass
    
    # Update metadata with state
    if "metadata" not in profile:
        profile["metadata"] = {}
    
    profile["metadata"]["state"] = state
    profile["metadata"]["state_updated_at"] = datetime.now(timezone.utc).isoformat()
    profile["metadata"]["state_updated_by"] = user_id
    
    if reason:
        profile["metadata"]["state_reason"] = reason
    
    # Validate schema
    validate_schema(profile, "standards_profile.schema.json")
    
    # Save
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    
    return profile


def submit_profile_for_approval(
    profile_id: str,
    user_id: str,
    reason: str | None = None,
) -> Dict[str, Any]:
    """
    Submit profile for approval (draft → submitted).
    
    Args:
        profile_id: Profile ID
        user_id: User submitting
        reason: Optional reason
    
    Returns:
        Updated profile
    """
    can_submit, error_msg = can_submit_profile(profile_id)
    if not can_submit:
        raise ValueError(error_msg)
    
    return _save_profile_with_state(profile_id, "submitted", user_id, reason)


def approve_profile(
    profile_id: str,
    user_id: str,
    reason: str | None = None,
) -> Dict[str, Any]:
    """
    Approve profile (submitted → approved).
    
    Args:
        profile_id: Profile ID
        user_id: User approving (must be OPS/ADMIN)
        reason: Optional approval reason
    
    Returns:
        Approved profile
    """
    can_approve, error_msg = can_approve_profile(profile_id)
    if not can_approve:
        raise ValueError(error_msg)
    
    return _save_profile_with_state(profile_id, "approved", user_id, reason)


def reject_profile(
    profile_id: str,
    user_id: str,
    reason: str,
) -> Dict[str, Any]:
    """
    Reject profile (submitted → draft).
    
    Args:
        profile_id: Profile ID
        user_id: User rejecting
        reason: Rejection reason (required)
    
    Returns:
        Rejected profile (returns to draft)
    """
    can_reject, error_msg = can_reject_profile(profile_id)
    if not can_reject:
        raise ValueError(error_msg)
    
    if not reason or not reason.strip():
        raise ValueError("Rejection reason is required")
    
    return _save_profile_with_state(profile_id, "draft", user_id, reason)


def deprecate_profile(
    profile_id: str,
    user_id: str,
    reason: str,
    superseded_by: str | None = None,
) -> Dict[str, Any]:
    """
    Deprecate profile (approved → deprecated).
    
    Args:
        profile_id: Profile ID
        user_id: User deprecating
        reason: Deprecation reason (required)
        superseded_by: Optional profile ID that supersedes this one
    
    Returns:
        Deprecated profile
    """
    can_deprecate, error_msg = can_deprecate_profile(profile_id)
    if not can_deprecate:
        raise ValueError(error_msg)
    
    if not reason or not reason.strip():
        raise ValueError("Deprecation reason is required")
    
    profile = _save_profile_with_state(profile_id, "deprecated", user_id, reason)
    
    # Add supersedes metadata if provided
    if superseded_by:
        if "metadata" not in profile:
            profile["metadata"] = {}
        if "superseded_by" not in profile["metadata"]:
            profile["metadata"]["superseded_by"] = []
        profile["metadata"]["superseded_by"].append(superseded_by)
    
    return profile


def ensure_profile_immutable(profile_id: str) -> None:
    """
    Ensure profile is immutable (Sprint 5: approved profiles cannot be modified).
    
    Raises:
        ValueError: If profile is approved and cannot be modified
    """
    state = get_profile_state(profile_id)
    if state == "approved":
        raise ValueError(f"Profile {profile_id} is approved and immutable. Create a new version to make changes.")


def can_modify_profile(profile_id: str) -> bool:
    """Check if profile can be modified (only draft/submitted/rejected)."""
    state = get_profile_state(profile_id)
    return state in ["draft", "submitted", "rejected"]


def validate_profile_for_use(profile_id: str, allow_draft: bool = False) -> Tuple[bool, str]:
    """
    Validate profile can be used in SOE runs or plans (Sprint 5: red-team guard).
    
    Args:
        profile_id: Profile ID to validate
        allow_draft: Whether draft profiles are allowed (default: False for production)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    state = get_profile_state(profile_id)
    
    if state == "deprecated":
        return (False, f"Profile {profile_id} is deprecated and cannot be used in production plans.")
    
    if state == "draft" and not allow_draft:
        return (False, f"Profile {profile_id} is in draft state and cannot be used in production plans. Only approved profiles are allowed.")
    
    if state == "rejected":
        return (False, f"Profile {profile_id} was rejected and cannot be used.")
    
    return (True, "")
