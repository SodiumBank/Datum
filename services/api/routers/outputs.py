"""Execution outputs API endpoints (Sprint 2: read-only intent)."""

from fastapi import APIRouter, Depends, HTTPException, status

from services.api.core.deps import require_role
from services.api.core.execution_outputs import (
    generate_all_execution_outputs,
    generate_lead_form_intent,
    generate_placement_intent,
    generate_programming_intent,
    generate_selective_solder_intent,
    generate_stencil_intent,
)
from services.api.core.storage import (
    get_plan,
    get_normalized_bom,
)

router = APIRouter()


@router.get("/{plan_id}")
def get_execution_outputs_endpoint(
    plan_id: str,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """
    Get execution outputs for a plan (Sprint 2: read-only intent).
    
    Returns stencil, placement, selective solder, lead form, and programming intents.
    NO machine files, NO production-ready artifacts.
    """
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Get upload_id from quote (would need to be stored in plan or retrieved from quote)
    quote_id = plan.get("quote_id")
    if not quote_id:
        raise HTTPException(status_code=400, detail="Plan missing quote_id")
    
    # Get gerber upload_id from quote metadata (stored in quote)
    from services.api.core.storage import get_quote
    quote = get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    upload_id = quote.get("gerber_upload_id") or quote.get("inputs", {}).get("gerber_upload_id")
    if not upload_id:
        raise HTTPException(status_code=400, detail="Quote missing gerber upload")
    
    # Get BOM items
    bom_items = get_normalized_bom(upload_id)
    
    # Generate all execution outputs
    outputs = generate_all_execution_outputs(upload_id, bom_items)
    
    return {
        "plan_id": plan_id,
        "quote_id": quote_id,
        "outputs": outputs,
        "note": "Sprint 2: Read-only intent - not production-ready",
    }


@router.get("/{plan_id}/stencil")
def get_stencil_intent_endpoint(
    plan_id: str,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Get stencil intent for a plan (Sprint 2: read-only)."""
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    quote_id = plan.get("quote_id")
    from services.api.core.storage import get_quote
    quote = get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    upload_id = quote.get("gerber_upload_id") or quote.get("inputs", {}).get("gerber_upload_id")
    if not upload_id:
        raise HTTPException(status_code=400, detail="Quote missing gerber upload")
    
    bom_items = get_normalized_bom(upload_id)
    return generate_stencil_intent(upload_id, bom_items)


@router.get("/{plan_id}/placement")
def get_placement_intent_endpoint(
    plan_id: str,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Get placement intent for a plan (Sprint 2: read-only)."""
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    quote_id = plan.get("quote_id")
    from services.api.core.storage import get_quote
    quote = get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    upload_id = quote.get("gerber_upload_id") or quote.get("inputs", {}).get("gerber_upload_id")
    if not upload_id:
        raise HTTPException(status_code=400, detail="Quote missing gerber upload")
    
    bom_items = get_normalized_bom(upload_id)
    return generate_placement_intent(upload_id, bom_items)


@router.get("/{plan_id}/selective-solder")
def get_selective_solder_intent_endpoint(
    plan_id: str,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Get selective solder intent for a plan (Sprint 2: read-only)."""
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    quote_id = plan.get("quote_id")
    from services.api.core.storage import get_quote
    quote = get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    upload_id = quote.get("gerber_upload_id") or quote.get("inputs", {}).get("gerber_upload_id")
    if not upload_id:
        raise HTTPException(status_code=400, detail="Quote missing gerber upload")
    
    bom_items = get_normalized_bom(upload_id)
    return generate_selective_solder_intent(upload_id, bom_items)


@router.get("/{plan_id}/lead-form")
def get_lead_form_intent_endpoint(
    plan_id: str,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Get lead form intent for a plan (Sprint 2: read-only)."""
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    quote_id = plan.get("quote_id")
    from services.api.core.storage import get_quote
    quote = get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    upload_id = quote.get("gerber_upload_id") or quote.get("inputs", {}).get("gerber_upload_id")
    if not upload_id:
        raise HTTPException(status_code=400, detail="Quote missing gerber upload")
    
    bom_items = get_normalized_bom(upload_id)
    return generate_lead_form_intent(upload_id, bom_items)


@router.get("/{plan_id}/programming")
def get_programming_intent_endpoint(
    plan_id: str,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Get programming intent for a plan (Sprint 2: read-only)."""
    plan = get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    quote_id = plan.get("quote_id")
    from services.api.core.storage import get_quote
    quote = get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    upload_id = quote.get("gerber_upload_id") or quote.get("inputs", {}).get("gerber_upload_id")
    if not upload_id:
        raise HTTPException(status_code=400, detail="Quote missing gerber upload")
    
    bom_items = get_normalized_bom(upload_id)
    return generate_programming_intent(upload_id, bom_items)
