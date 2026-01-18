"""Compliance traceability API endpoints (Sprint 4)."""

from fastapi import APIRouter, Depends, HTTPException, status

from services.api.core.deps import require_role
from services.api.core.compliance_trace import get_plan_compliance_trace

router = APIRouter()


@router.get("/plans/{plan_id}/compliance-trace")
def get_compliance_trace_endpoint(
    plan_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """
    Get compliance traceability for a plan (Sprint 4).
    
    Returns mapping of plan steps/tests/evidence to:
    - Source standards and clauses
    - Profile source and layer
    - SOE decision IDs
    - Rule IDs and packs
    """
    try:
        trace = get_plan_compliance_trace(plan_id)
        return trace
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance trace: {str(e)}",
        ) from e


@router.get("/plans/{plan_id}/steps/{step_id}/compliance")
def get_step_compliance_endpoint(
    plan_id: str,
    step_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """
    Get compliance traceability for a specific step (Sprint 4).
    
    Returns why this step exists and which standards require it.
    """
    from services.api.core.storage import get_plan, get_soe_run
    from services.api.core.compliance_trace import build_compliance_trace_for_step
    
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found: {plan_id}",
        )
    
    # Find step
    step = next((s for s in plan.get("steps", []) if s.get("step_id") == step_id), None)
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step not found: {step_id}",
        )
    
    # Get SOERun
    soe_run_id = plan.get("soe_run_id")
    soe_run = None
    if soe_run_id:
        soe_run = get_soe_run(soe_run_id)
    
    # Build trace
    trace = build_compliance_trace_for_step(step, soe_run)
    
    return {
        "step_id": step_id,
        "step_type": step.get("type"),
        "step_title": step.get("title"),
        "compliance_trace": trace,
    }
