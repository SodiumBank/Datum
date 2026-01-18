"""Datum Plan API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any, Dict

from services.api.core.deps import require_role
from services.api.core.plan_generator import generate_plan
from services.api.core.storage import get_plan, list_plans, save_audit_event
from services.api.core.schema_validation import validate_schema
import secrets
import string
from datetime import datetime, timezone

router = APIRouter()


def _generate_id(prefix: str = "audit") -> str:
    """Generate a unique ID."""
    random_suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    return f"{prefix}_{random_suffix}"


class GeneratePlanRequest(BaseModel):
    """Request model for generating a plan."""
    quote_id: str
    ruleset_version: int = 1
    org_id: str | None = None
    design_id: str | None = None


@router.post("/generate")
def generate_plan_endpoint(
    request: GeneratePlanRequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """
    Generate a DatumPlan from a quote and ruleset.
    
    Returns a DatumPlan with steps derived from rules and quote assumptions.
    """
    try:
        plan = generate_plan(
            quote_id=request.quote_id,
            ruleset_version=request.ruleset_version,
            org_id=request.org_id,
            design_id=request.design_id,
        )
        
        # Create audit event
        timestamp = datetime.now(timezone.utc).isoformat()
        audit_event = {
            "id": _generate_id("audit"),
            "entity_type": "DATUM_PLAN",
            "entity_id": plan["id"],
            "action": "CREATE",
            "user_id": auth.get("sub", "unknown"),
            "timestamp": timestamp,
            "reason": f"Plan generated from quote {request.quote_id}",
        }
        save_audit_event(audit_event)
        
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plan generation failed: {str(e)}",
        ) from e


@router.get("/{plan_id}")
def get_plan_endpoint(
    plan_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Get a specific plan by ID (Sprint 2: read-only intent layer)."""
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}",
        )
    return plan


@router.get("/quote/{quote_id}")
def get_plan_by_quote_endpoint(
    quote_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Get plan by quote ID (Sprint 2: read-only intent layer)."""
    plans = list_plans(quote_id=quote_id)
    if not plans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found for quote: {quote_id}",
        )
    # Return most recent plan
    plans.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return plans[0]


@router.get("")
def list_plans_endpoint(
    quote_id: str | None = None,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """List plans, optionally filtered by quote_id."""
    plans = list_plans(quote_id=quote_id)
    return {"plans": plans, "count": len(plans)}


class UpdatePlanStepsRequest(BaseModel):
    """Request model for updating plan steps."""
    steps: list[dict]
    override_reason: str | None = None


@router.post("/{plan_id}/steps")
def update_plan_steps(
    plan_id: str,
    request: UpdatePlanStepsRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """
    Update plan steps with validation for locked sequences.
    
    Locked steps cannot be reordered without an override reason and audit event.
    """
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}",
        )
    
    # Check if plan is locked
    from services.api.core.revision_manager import check_locked
    if check_locked("DATUM_PLAN", plan_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Plan {plan_id} is locked. Create a new revision to modify.",
        )
    
    # Validate step reorder
    from services.api.core.plan_validator import (
        validate_step_reorder,
        validate_locked_sequence_integrity,
    )
    
    is_valid, error_msg = validate_step_reorder(
        original_plan=plan,
        updated_steps=request.steps,
        override_reason=request.override_reason,
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
    
    # Validate locked sequence integrity
    is_valid, error_msg = validate_locked_sequence_integrity(request.steps)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
    
    # Update plan
    plan["steps"] = request.steps
    from datetime import datetime, timezone
    plan["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_plan(plan)
    
    # Create audit event if override was used
    if request.override_reason and request.override_reason.strip():
        timestamp = datetime.now(timezone.utc).isoformat()
        audit_event = {
            "id": _generate_id("audit"),
            "entity_type": "DATUM_PLAN",
            "entity_id": plan_id,
            "action": "OVERRIDE",
            "user_id": auth.get("sub", "unknown"),
            "timestamp": timestamp,
            "reason": request.override_reason,
            "delta": {"step_count": len(request.steps)},
        }
        save_audit_event(audit_event)
    
    # Create update audit event
    timestamp = datetime.now(timezone.utc).isoformat()
    audit_event = {
        "id": _generate_id("audit"),
        "entity_type": "DATUM_PLAN",
        "entity_id": plan_id,
        "action": "UPDATE",
        "user_id": auth.get("sub", "unknown"),
        "timestamp": timestamp,
        "reason": "Plan steps updated",
    }
    save_audit_event(audit_event)
    
    return {"plan": plan}
