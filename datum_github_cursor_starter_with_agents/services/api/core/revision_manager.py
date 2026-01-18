"""Revision manager for creating and managing DatumRevision records."""

import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, List

from services.api.core.storage import (
    save_revision,
    get_revision,
    list_revisions,
    get_lock,
    save_audit_event,
)
from services.api.core.schema_validation import validate_schema


def _generate_id(prefix: str = "rev") -> str:
    """Generate a unique ID."""
    random_suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    return f"{prefix}_{random_suffix}"


def create_revision(
    org_id: str,
    design_id: str,
    reason: str,
    created_by: str,
) -> Dict[str, Any]:
    """
    Create a new DatumRevision.
    
    Args:
        org_id: Organization ID
        design_id: Design ID
        reason: Reason for creating this revision
        created_by: User ID who created the revision
    
    Returns:
        DatumRevision object
    """
    revision_id = _generate_id("rev")
    timestamp = datetime.now(timezone.utc).isoformat()
    
    revision: Dict[str, Any] = {
        "id": revision_id,
        "org_id": org_id,
        "design_id": design_id,
        "created_at": timestamp,
        "created_by": created_by,
        "reason": reason,
    }
    
    # Validate against schema
    try:
        validate_schema(revision, "datum_revision.schema.json")
    except Exception as e:
        raise ValueError(f"Revision schema validation failed: {e}") from e
    
    # Save revision
    save_revision(revision)
    
    # Create audit event
    audit_event = {
        "id": _generate_id("audit"),
        "entity_type": "DATUM_REVISION",
        "entity_id": revision_id,
        "action": "CREATE",
        "user_id": created_by,
        "timestamp": timestamp,
        "reason": reason,
    }
    save_audit_event(audit_event)
    
    return revision


def check_locked(entity_type: str, entity_id: str) -> bool:
    """
    Check if an entity is locked.
    
    Args:
        entity_type: Type of entity (DATUM_QUOTE, DATUM_PLAN, etc.)
        entity_id: ID of the entity
    
    Returns:
        True if locked, False otherwise
    """
    lock = get_lock(entity_type, entity_id)
    return lock is not None


def ensure_not_locked(entity_type: str, entity_id: str) -> None:
    """
    Raise an error if entity is locked.
    
    Args:
        entity_type: Type of entity
        entity_id: ID of the entity
    
    Raises:
        ValueError: If entity is locked
    """
    if check_locked(entity_type, entity_id):
        raise ValueError(
            f"{entity_type} {entity_id} is locked. Create a new revision to modify."
        )


def create_revision_for_update(
    org_id: str,
    design_id: str,
    entity_type: str,
    entity_id: str,
    reason: str,
    created_by: str,
) -> Dict[str, Any]:
    """
    Create a new revision when updating a locked entity.
    
    This function:
    1. Checks if entity is locked
    2. If locked, creates a new revision
    3. Creates audit event
    
    Args:
        org_id: Organization ID
        design_id: Design ID
        entity_type: Type of entity being updated
        entity_id: ID of the entity
        reason: Reason for creating new revision
        created_by: User ID
    
    Returns:
        New DatumRevision object
    """
    # Check if locked
    if check_locked(entity_type, entity_id):
        # Create new revision
        revision = create_revision(
            org_id=org_id,
            design_id=design_id,
            reason=f"New revision for {entity_type} {entity_id}: {reason}",
            created_by=created_by,
        )
        
        # Create audit event for revision creation due to update
        timestamp = datetime.now(timezone.utc).isoformat()
        audit_event = {
            "id": _generate_id("audit"),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": "NEW_REVISION",
            "user_id": created_by,
            "timestamp": timestamp,
            "reason": reason,
            "delta": {"new_revision_id": revision["id"]},
        }
        save_audit_event(audit_event)
        
        return revision
    
    return None
