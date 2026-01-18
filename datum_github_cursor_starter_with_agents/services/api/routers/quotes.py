import secrets
import string
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from jsonschema import ValidationError
from services.api.core.deps import require_role
from services.api.core.schema_validation import validate_schema
from services.api.core.storage import (
    get_board_metrics,
    get_normalized_bom,
    get_gerber_files,
    save_quote,
    get_quote,
    list_quotes,
    save_lock,
    get_lock,
    save_audit_event,
    save_soe_run,
    get_soe_run,
)
from services.api.core.pricing import calculate_pricing, calculate_inputs_fingerprint, PricingInputs

router = APIRouter()


def _generate_id(prefix: str = "qte") -> str:
    """Generate a unique ID."""
    random_suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    return f"{prefix}_{random_suffix}"


class QuoteEstimateRequest(BaseModel):
    """Request model for quote estimate."""
    gerber_upload_id: str
    bom_upload_id: str | None = None
    quantity: int = 1
    assumptions: dict | None = None
    org_id: str = "org_dev_001"  # Placeholder - would come from auth
    design_id: str | None = None  # Optional - can be generated
    industry_profile: str | None = None  # Optional - for SOE evaluation
    hardware_class: str | None = None  # Optional - for SOE evaluation


@router.post("/estimate")
def estimate_quote(
    request: QuoteEstimateRequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN"))
):
    """
    Generate deterministic quote estimate based on board metrics and BOM.
    
    Returns DatumQuote with cost breakdown, lead time, and risk factors.
    Same inputs produce identical quotes (deterministic).
    """
    # Fetch board metrics
    board_metrics = get_board_metrics(request.gerber_upload_id)
    if not board_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board metrics not found for gerber_upload_id: {request.gerber_upload_id}",
        )
    
    # Fetch Gerber files list for DRC checks
    gerber_files = get_gerber_files(request.gerber_upload_id)
    if not gerber_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gerber files not found for upload_id: {request.gerber_upload_id}",
        )
    
    # Fetch normalized BOM if provided
    bom_items = None
    if request.bom_upload_id:
        bom_items = get_normalized_bom(request.bom_upload_id)
        if bom_items is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Normalized BOM not found for bom_upload_id: {request.bom_upload_id}",
            )
    
    # Prepare pricing inputs
    pricing_inputs: PricingInputs = {
        "gerber_upload_id": request.gerber_upload_id,
        "bom_upload_id": request.bom_upload_id,
        "board_metrics": board_metrics,
        "bom_items": bom_items,
        "gerber_files": gerber_files,
        "quantity": request.quantity,
        "assumptions": request.assumptions or {},
    }
    
    # Get SOE cost modifiers if SOERun exists (will be loaded later if industry_profile provided)
    soe_cost_modifiers = None
    
    # Calculate pricing (deterministic)
    pricing_result = calculate_pricing(pricing_inputs, soe_cost_modifiers=soe_cost_modifiers)
    
    # Calculate inputs fingerprint (deterministic hash of inputs)
    inputs_fingerprint = calculate_inputs_fingerprint(pricing_inputs)
    
    # Generate IDs
    quote_id = _generate_id("quote")
    revision_id = _generate_id("rev")
    design_id = request.design_id or _generate_id("design")
    
    # Generate timestamp
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Build quote payload
    payload = {
        "id": quote_id,
        "org_id": request.org_id,
        "design_id": design_id,
        "tier": "TIER_1",
        "revision_id": revision_id,
        "quote_version": 1,  # First version of this quote
        "inputs_fingerprint": inputs_fingerprint,
        "quantity": request.quantity,
        "lead_time_days": pricing_result["lead_time_days"],
        "cost_breakdown": {
            "currency": "USD",
            "total": pricing_result["total"],
            "lines": pricing_result["lines"],
        },
        "risk_factors": pricing_result.get("risk_factors", []),
        "assumptions": request.assumptions or {"assembly_sides": ["TOP"]},
        "status": "ESTIMATED",
        "created_at": timestamp,
    }
    
    # Validate against schema
    try:
        validate_schema(payload, "datum_quote.schema.json")
    except ValidationError as exc:
        error_msg = getattr(exc, "message", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quote schema validation failed: {error_msg}",
        ) from exc
    
    # Save quote
    save_quote(payload)
    
    # Create audit event
    audit_event = {
        "id": _generate_id("audit"),
        "entity_type": "DATUM_QUOTE",
        "entity_id": quote_id,
        "action": "CREATE",
        "user_id": auth.get("sub", "unknown"),
        "timestamp": timestamp,
        "reason": "Quote generated",
    }
    save_audit_event(audit_event)
    
    # Evaluate SOE if industry_profile is provided
    soe_run = None
    if request.industry_profile:
        try:
            from services.api.core.soe_engine import evaluate_soe
            from services.api.core.supply_chain import analyze_bom_risks
            
            # Extract SOE inputs from quote context
            bom_risk_flags = []
            if bom_items:
                risks = analyze_bom_risks(bom_items)
                if risks.get("has_long_lead"):
                    bom_risk_flags.append("LONG_LEAD")
                if risks.get("has_eee"):
                    bom_risk_flags.append("EEE")
            
            soe_inputs = {
                "processes": request.assumptions.get("assembly_sides", ["TOP"]) if request.assumptions else ["TOP"],
                "tests_requested": [],
                "materials": [],
                "bom_risk_flags": bom_risk_flags,
            }
            
            soe_run = evaluate_soe(
                industry_profile=request.industry_profile,
                inputs=soe_inputs,
                hardware_class=request.hardware_class,
            )
            
            # Apply SOE cost modifiers to pricing (recalculate if needed)
            if soe_run.get("cost_modifiers"):
                soe_cost_modifiers = soe_run["cost_modifiers"]
                pricing_result = calculate_pricing(pricing_inputs, soe_cost_modifiers=soe_cost_modifiers)
                # Update quote payload with recalculated costs
                payload["cost_breakdown"]["total"] = pricing_result["total"]
                payload["cost_breakdown"]["lines"] = pricing_result["lines"]
            
            # Attach SOERun metadata to quote
            payload["soe_run"] = {
                "soe_version": soe_run["soe_version"],
                "industry_profile": soe_run["industry_profile"],
                "active_packs": soe_run["active_packs"],
                "decision_count": len(soe_run["decisions"]),
                "gate_status": soe_run["gates"][0]["status"] if soe_run["gates"] else "open",
            }
            
            # Check if release is blocked by SOE
            if soe_run["gates"] and soe_run["gates"][0].get("status") == "blocked":
                payload["status"] = "SOE_BLOCKED"  # New status for SOE-blocked quotes
            
            # Save SOERun with link to quote
            soe_run["metadata"] = {
                "quote_id": quote_id,
                "org_id": request.org_id,
                "design_id": design_id,
            }
            save_soe_run(soe_run)
        except Exception as e:
            # Log error but don't fail quote generation
            print(f"Warning: SOE evaluation failed: {e}")
    
    return payload


@router.get("")
def list_quotes_endpoint(
    status: str | None = None,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """
    List quotes, optionally filtered by status.
    
    Ops can see all quotes. Filter by status=ESTIMATED to see quotes needing review.
    """
    quotes = list_quotes(status_filter=status)
    return {"quotes": quotes, "count": len(quotes)}


@router.get("/{quote_id}")
def get_quote_endpoint(
    quote_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Get a specific quote by ID."""
    quote = get_quote(quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote not found: {quote_id}",
        )
    return quote


class LockQuoteRequest(BaseModel):
    """Request model for locking a quote."""
    lock_reason: str
    requires_contract: bool = False


@router.post("/{quote_id}/lock")
def lock_quote(
    quote_id: str,
    request: LockQuoteRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """
    Lock a quote (make it immutable).
    
    Once locked, the quote cannot be modified. A new revision must be created.
    Creates a DatumLock record and emits DatumAuditEvent.
    
    Note: Quotes blocked by SOE gates cannot be locked until SOE requirements are met.
    """
    quote = get_quote(quote_id)
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote not found: {quote_id}",
        )
    
    # Check if blocked by SOE
    soe_run = get_soe_run(quote_id=quote_id)
    if soe_run and soe_run.get("gates"):
        gate_status = soe_run["gates"][0].get("status")
        if gate_status == "blocked":
            blocked_by = soe_run["gates"][0].get("blocked_by", [])
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Quote {quote_id} is blocked by SOE gates. Decisions: {', '.join(blocked_by)}",
            )
    
    # Check if already locked
    existing_lock = get_lock("DATUM_QUOTE", quote_id)
    if existing_lock:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Quote {quote_id} is already locked",
        )
    
    # Create lock
    timestamp = datetime.now(timezone.utc).isoformat()
    lock_id = _generate_id("lock")
    lock = {
        "id": lock_id,
        "entity_type": "DATUM_QUOTE",
        "entity_id": quote_id,
        "locked_by": auth.get("sub", "unknown"),
        "locked_at": timestamp,
        "lock_reason": request.lock_reason,
        "requires_contract": request.requires_contract,
    }
    save_lock(lock)
    
    # Update quote status
    quote["status"] = "LOCKED"
    quote["updated_at"] = timestamp
    save_quote(quote)
    
    # Create audit event
    audit_event = {
        "id": _generate_id("audit"),
        "entity_type": "DATUM_QUOTE",
        "entity_id": quote_id,
        "action": "LOCK",
        "user_id": auth.get("sub", "unknown"),
        "timestamp": timestamp,
        "reason": request.lock_reason,
    }
    save_audit_event(audit_event)
    
    return {"lock": lock, "quote": quote}
