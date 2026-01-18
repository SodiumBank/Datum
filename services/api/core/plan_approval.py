"""DatumPlan approval workflow (Sprint 3).

State machine: draft → submitted → approved/rejected
"""

from datetime import datetime, timezone
from typing import Dict, Any, Tuple

from services.api.core.storage import get_plan, save_plan, save_audit_event


def can_submit_plan(plan: Dict[str, Any]) -> Tuple[bool, str]:
    """Check if plan can be submitted for approval."""
    if plan.get("state") != "draft":
        return (False, f"Plan is in {plan.get('state')} state. Only draft plans can be submitted.")
    
    # Check that plan has steps
    if not plan.get("steps"):
        return (False, "Plan must have at least one step before submission.")
    
    return (True, "")


def can_approve_plan(plan: Dict[str, Any]) -> Tuple[bool, str]:
    """Check if plan can be approved."""
    if plan.get("state") != "submitted":
        return (False, f"Plan is in {plan.get('state')} state. Only submitted plans can be approved.")
    
    return (True, "")


def can_reject_plan(plan: Dict[str, Any]) -> Tuple[bool, str]:
    """Check if plan can be rejected."""
    if plan.get("state") != "submitted":
        return (False, f"Plan is in {plan.get('state')} state. Only submitted plans can be rejected.")
    
    return (True, "")


def submit_plan_for_approval(
    plan_id: str,
    user_id: str,
    reason: str | None = None,
) -> Dict[str, Any]:
    """
    Submit plan for approval (draft → submitted).
    
    Args:
        plan_id: Plan ID
        user_id: User submitting
        reason: Optional reason
    
    Returns:
        Updated plan
    """
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")
    
    can_submit, error_msg = can_submit_plan(plan)
    if not can_submit:
        raise ValueError(error_msg)
    
    # Update state
    plan["state"] = "submitted"
    plan["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Save
    save_plan(plan)
    
    # Create audit event
    timestamp = datetime.now(timezone.utc).isoformat()
    audit_event = {
        "id": f"audit_{plan_id}_{timestamp}",
        "entity_type": "DATUM_PLAN",
        "entity_id": plan_id,
        "action": "SUBMIT",
        "user_id": user_id,
        "timestamp": timestamp,
        "reason": reason or "Plan submitted for approval",
    }
    save_audit_event(audit_event)
    
    return plan


def approve_plan(
    plan_id: str,
    user_id: str,
    reason: str | None = None,
) -> Dict[str, Any]:
    """
    Approve plan (submitted → approved).
    
    Args:
        plan_id: Plan ID
        user_id: User approving (must be OPS/ADMIN)
        reason: Optional approval reason
    
    Returns:
        Approved plan
    """
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")
    
    can_approve, error_msg = can_approve_plan(plan)
    if not can_approve:
        raise ValueError(error_msg)
    
    # Update state
    plan["state"] = "approved"
    plan["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Lock plan when approved (approved plans are immutable)
    plan["locked"] = True
    plan["lock_id"] = f"lock_approved_{plan_id}_{datetime.now(timezone.utc).isoformat()}"
    
    # Save
    save_plan(plan)
    
    # Create audit event
    timestamp = datetime.now(timezone.utc).isoformat()
    audit_event = {
        "id": f"audit_{plan_id}_{timestamp}",
        "entity_type": "DATUM_PLAN",
        "entity_id": plan_id,
        "action": "APPROVE",
        "user_id": user_id,
        "timestamp": timestamp,
        "reason": reason or "Plan approved",
    }
    save_audit_event(audit_event)
    
    return plan


def reject_plan(
    plan_id: str,
    user_id: str,
    reason: str,
) -> Dict[str, Any]:
    """
    Reject plan (submitted → draft).
    
    Args:
        plan_id: Plan ID
        user_id: User rejecting (must be OPS/ADMIN)
        reason: Rejection reason (required)
    
    Returns:
        Rejected plan (returns to draft)
    """
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")
    
    can_reject, error_msg = can_reject_plan(plan)
    if not can_reject:
        raise ValueError(error_msg)
    
    if not reason or not reason.strip():
        raise ValueError("Rejection reason is required")
    
    # Update state (return to draft)
    plan["state"] = "draft"
    plan["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Save
    save_plan(plan)
    
    # Create audit event
    timestamp = datetime.now(timezone.utc).isoformat()
    audit_event = {
        "id": f"audit_{plan_id}_{timestamp}",
        "entity_type": "DATUM_PLAN",
        "entity_id": plan_id,
        "action": "REJECT",
        "user_id": user_id,
        "timestamp": timestamp,
        "reason": reason,
    }
    save_audit_event(audit_event)
    
    return plan
