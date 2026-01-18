"""Rules engine API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any, Dict, List

from services.api.core.deps import require_role
from services.api.core.rules_engine import (
    evaluate_rules,
    FeatureContext,
    load_ruleset_info,
)
from services.api.core.storage import (
    get_board_metrics,
    get_normalized_bom,
    get_gerber_files,
    get_quote,
)

router = APIRouter()


class EvaluateRulesRequest(BaseModel):
    """Request model for evaluating rules."""
    gerber_upload_id: str
    bom_upload_id: str | None = None
    quote_id: str | None = None
    ruleset_version: int = 1
    tier: str = "TIER_1"


@router.post("/evaluate")
def evaluate_rules_endpoint(
    request: EvaluateRulesRequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """
    Evaluate rules against extracted features from uploaded files.
    
    Returns a list of matched rules with their traces (rule_id, justification, etc.).
    """
    # Load features
    board_metrics = get_board_metrics(request.gerber_upload_id)
    if not board_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board metrics not found for gerber_upload_id: {request.gerber_upload_id}",
        )
    
    bom_items = None
    if request.bom_upload_id:
        bom_data = get_normalized_bom(request.bom_upload_id)
        if bom_data:
            bom_items = bom_data.get("items")
    
    gerber_files = get_gerber_files(request.gerber_upload_id)
    
    quote = None
    if request.quote_id:
        quote = get_quote(request.quote_id)
    
    # Extract assumptions from quote if available
    assumptions = None
    if quote:
        assumptions = quote.get("assumptions")
    
    # Build context
    context: FeatureContext = {
        "board_metrics": board_metrics,
        "bom_items": bom_items,
        "quote": quote,
        "assumptions": assumptions,
        "gerber_files": gerber_files,
    }
    
    # Evaluate rules
    traces = evaluate_rules(
        context,
        ruleset_version=request.ruleset_version,
        tier=request.tier,
    )
    
    return {
        "ruleset_version": request.ruleset_version,
        "tier": request.tier,
        "traces": traces,
        "matched_count": len(traces),
    }


@router.get("/ruleset/{ruleset_version}")
def get_ruleset_endpoint(
    ruleset_version: int,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Get ruleset metadata and rules."""
    try:
        info = load_ruleset_info(ruleset_version)
        return info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
