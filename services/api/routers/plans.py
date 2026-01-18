"""Datum Plan API endpoints (Sprint 3: Editable & Governed)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any, Dict
from datetime import datetime, timezone

from services.api.core.deps import require_role
from services.api.core.plan_generator import generate_plan
from services.api.core.storage import get_plan, list_plans, save_audit_event
from services.api.core.schema_validation import validate_schema
import secrets
import string

router = APIRouter()


def _generate_id(prefix: str = "audit") -> str:
    """Generate a unique ID."""
    random_suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    return f"{prefix}_{random_suffix}"


class GeneratePlanRequest(BaseModel):
    """Request model for generating a plan."""
    quote_id: str
    soe_run: dict | None = None
    ruleset_version: int = 1
    org_id: str | None = None
    design_id: str | None = None


@router.post("/generate")
def generate_plan_endpoint(
    request: GeneratePlanRequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """
    Generate a DatumPlan from SOERun + quote (Sprint 3: creates draft plan).
    
    Returns a DatumPlan with steps derived from SOE decisions and rules.
    """
    try:
        plan = generate_plan(
            quote_id=request.quote_id,
            soe_run=request.soe_run,
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
    """Get a specific plan by ID (Sprint 3: returns latest version)."""
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
    """Get plan by quote ID (Sprint 3: returns latest version)."""
    plans = list_plans(quote_id=quote_id)
    if not plans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found for quote: {quote_id}",
        )
    # Return most recent version
    plans.sort(key=lambda p: (p.get("version", 1), p.get("created_at", "")), reverse=True)
    return plans[0]


@router.get("")
def list_plans_endpoint(
    quote_id: str | None = None,
    state: str | None = None,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """List plans, optionally filtered by quote_id or state (Sprint 3)."""
    plans = list_plans(quote_id=quote_id)
    
    # Filter by state if provided
    if state:
        plans = [p for p in plans if p.get("state") == state]
    
    return {"plans": plans, "count": len(plans)}


class EditPlanRequest(BaseModel):
    """Request model for editing a plan (Sprint 3)."""
    steps: list[dict] | None = None
    tests: list[dict] | None = None
    evidence_intent: list[dict] | None = None
    notes: str | None = None
    eee_requirements: dict | None = None
    edit_reason: str
    allow_overrides: bool = False
    override_reason: str | None = None


@router.patch("/{plan_id}")
def edit_plan_endpoint(
    plan_id: str,
    request: EditPlanRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """
    Edit a DatumPlan (Sprint 3: Controlled editing with SOE constraint preservation).
    
    Allows editing non-SOE fields. SOE-required steps/tests/evidence can only be
    modified with explicit override and reason.
    """
    from services.api.core.plan_editor import apply_plan_edit
    
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}",
        )
    
    # Build edits dict
    edits = {}
    if request.steps is not None:
        edits["steps"] = request.steps
    if request.tests is not None:
        edits["tests"] = request.tests
    if request.evidence_intent is not None:
        edits["evidence_intent"] = request.evidence_intent
    if request.notes is not None:
        edits["notes"] = request.notes
    if request.eee_requirements is not None:
        edits["eee_requirements"] = request.eee_requirements
    
    try:
        # Apply edit (creates new version)
        edited_plan = apply_plan_edit(
            plan=plan,
            edits=edits,
            user_id=auth.get("sub", "unknown"),
            edit_reason=request.edit_reason,
            allow_overrides=request.allow_overrides,
            override_reason=request.override_reason,
        )
        
        # Save new version
        save_plan(edited_plan)
        
        # Create audit event
        timestamp = datetime.now(timezone.utc).isoformat()
        audit_event = {
            "id": _generate_id("audit"),
            "entity_type": "DATUM_PLAN",
            "entity_id": plan_id,
            "action": "EDIT",
            "user_id": auth.get("sub", "unknown"),
            "timestamp": timestamp,
            "reason": request.edit_reason,
            "version": edited_plan.get("version"),
            "overrides": edited_plan.get("edit_metadata", {}).get("overrides", []),
        }
        save_audit_event(audit_event)
        
        return edited_plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plan edit failed: {str(e)}",
        ) from e


@router.get("/{plan_id}/versions")
def get_plan_versions_endpoint(
    plan_id: str,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Get all versions of a plan (Sprint 3)."""
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}",
        )
    
    quote_id = plan.get("quote_id")
    if not quote_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan missing quote_id",
        )
    
    # Get all versions for this quote (same quote_id = same plan, different versions)
    all_plans = list_plans(quote_id=quote_id)
    
    # Sort by version
    all_plans.sort(key=lambda p: p.get("version", 1))
    
    return {"plan_id": plan_id, "versions": all_plans, "count": len(all_plans)}


@router.get("/{plan_id}/versions/{version}")
def get_plan_version_endpoint(
    plan_id: str,
    version: int,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Get specific version of a plan (Sprint 3)."""
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}",
        )
    
    quote_id = plan.get("quote_id")
    all_plans = list_plans(quote_id=quote_id)
    
    # Find version
    target_plan = next((p for p in all_plans if p.get("version") == version), None)
    if not target_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version} not found for plan {plan_id}",
        )
    
    return target_plan


@router.get("/{plan_id}/diff")
def get_plan_diff_endpoint(
    plan_id: str,
    from_version: int | None = None,
    to_version: int | None = None,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Get diff between two plan versions (Sprint 3)."""
    from services.api.core.plan_editor import create_plan_diff
    
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}",
        )
    
    quote_id = plan.get("quote_id")
    all_plans = list_plans(quote_id=quote_id)
    
    # Determine versions
    if from_version is None:
        # Compare with previous version
        current_version = plan.get("version", 1)
        from_version = max(1, current_version - 1)
    if to_version is None:
        to_version = plan.get("version", 1)
    
    # Find plans
    plan_v1 = next((p for p in all_plans if p.get("version") == from_version), None)
    plan_v2 = next((p for p in all_plans if p.get("version") == to_version), None)
    
    if not plan_v1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {from_version} not found",
        )
    if not plan_v2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {to_version} not found",
        )
    
    diff = create_plan_diff(plan_v1, plan_v2)
    
    return {
        "from_version": from_version,
        "to_version": to_version,
        "diff": diff,
    }


class SubmitPlanRequest(BaseModel):
    """Request model for submitting plan for approval."""
    reason: str | None = None


class ApprovePlanRequest(BaseModel):
    """Request model for approving plan."""
    reason: str | None = None


class RejectPlanRequest(BaseModel):
    """Request model for rejecting plan."""
    reason: str


@router.post("/{plan_id}/submit")
def submit_plan_endpoint(
    plan_id: str,
    request: SubmitPlanRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Submit plan for approval (Sprint 3: draft → submitted)."""
    from services.api.core.plan_approval import submit_plan_for_approval
    
    try:
        plan = submit_plan_for_approval(
            plan_id=plan_id,
            user_id=auth.get("sub", "unknown"),
            reason=request.reason,
        )
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/{plan_id}/approve")
def approve_plan_endpoint(
    plan_id: str,
    request: ApprovePlanRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Approve plan (Sprint 3: submitted → approved)."""
    from services.api.core.plan_approval import approve_plan
    
    try:
        plan = approve_plan(
            plan_id=plan_id,
            user_id=auth.get("sub", "unknown"),
            reason=request.reason,
        )
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/{plan_id}/reject")
def reject_plan_endpoint(
    plan_id: str,
    request: RejectPlanRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Reject plan (Sprint 3: submitted → draft)."""
    from services.api.core.plan_approval import reject_plan
    
    try:
        plan = reject_plan(
            plan_id=plan_id,
            user_id=auth.get("sub", "unknown"),
            reason=request.reason,
        )
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


class OptimizePlanRequest(BaseModel):
    """Request model for optimizing plan."""
    objective: str = "throughput"  # "throughput", "cost", "resource"


@router.post("/{plan_id}/optimize")
def optimize_plan_endpoint(
    plan_id: str,
    request: OptimizePlanRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Optimize plan step ordering (Sprint 3: preserves SOE constraints)."""
    from services.api.core.plan_optimizer import optimize_plan_steps, generate_optimization_summary
    
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}",
        )
    
    # Cannot optimize approved plans (they're locked)
    if plan.get("state") == "approved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approved plans cannot be optimized. Create a new version.",
        )
    
    try:
        # Optimize
        optimized_plan = optimize_plan_steps(plan, objective=request.objective)
        
        # Save optimized version
        save_plan(optimized_plan)
        
        # Generate summary
        summary = generate_optimization_summary(plan, optimized_plan)
        
        # Create audit event
        timestamp = datetime.now(timezone.utc).isoformat()
        audit_event = {
            "id": _generate_id("audit"),
            "entity_type": "DATUM_PLAN",
            "entity_id": plan_id,
            "action": "OPTIMIZE",
            "user_id": auth.get("sub", "unknown"),
            "timestamp": timestamp,
            "reason": f"Optimized for {request.objective}",
            "version": optimized_plan.get("version"),
        }
        save_audit_event(audit_event)
        
        return {
            "plan": optimized_plan,
            "summary": summary,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}",
        ) from e


@router.get("/{plan_id}/export/csv")
def export_plan_csv_endpoint(
    plan_id: str,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Export plan to CSV (Sprint 3: only approved plans)."""
    from services.api.core.plan_exporter import export_plan_to_csv
    from fastapi.responses import Response
    
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}",
        )
    
    try:
        csv_content = export_plan_to_csv(plan)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="plan_{plan_id}_v{plan.get("version", 1)}.csv"'
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{plan_id}/export/json")
def export_plan_json_endpoint(
    plan_id: str,
    include_execution_outputs: bool = False,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Export plan to JSON (Sprint 3: only approved plans)."""
    from services.api.core.plan_exporter import export_plan_to_json
    import json
    
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}",
        )
    
    try:
        export_data = export_plan_to_json(plan, include_execution_outputs=include_execution_outputs)
        return export_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{plan_id}/export/placement-csv")
def export_placement_csv_endpoint(
    plan_id: str,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Export placement data to CSV (Sprint 3: machine-readable format)."""
    from services.api.core.plan_exporter import export_placement_csv
    from services.api.core.execution_outputs import generate_placement_intent
    from services.api.core.storage import get_quote, get_normalized_bom
    from fastapi.responses import Response
    
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}",
        )
    
    # Get execution outputs
    quote = get_quote(plan.get("quote_id"))
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found",
        )
    
    upload_id = quote.get("gerber_upload_id") or quote.get("inputs", {}).get("gerber_upload_id")
    if not upload_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quote missing gerber upload",
        )
    
    bom_items = get_normalized_bom(upload_id)
    placement_output = generate_placement_intent(upload_id, bom_items)
    
    try:
        csv_content = export_placement_csv(plan, placement_output)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="placement_{plan_id}_v{plan.get("version", 1)}.csv"'
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
