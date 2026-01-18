"""SOE (Standards Overlay Engine) API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any, Dict, List

from services.api.core.deps import require_role
from services.api.core.soe_engine import evaluate_soe, generate_why_explanation
from services.api.core.soe_audit import export_audit_manifest, create_decision_log

router = APIRouter()


class EvaluateSOERequest(BaseModel):
    """Request model for evaluating SOE (Sprint 4: supports active_profiles)."""
    industry_profile: str
    hardware_class: str | None = None
    inputs: Dict[str, Any]
    additional_packs: List[str] | None = None
    active_profiles: List[str] | None = None  # Sprint 4: Profile stack (BASE/DOMAIN/CUSTOMER_OVERRIDE)


@router.post("/evaluate")
def evaluate_soe_endpoint(
    request: EvaluateSOERequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """
    Evaluate SOE rules and generate SOERun.
    
    Returns decisions, gates, evidence requirements, and cost modifiers
    based on industry profile and standards packs.
    """
    try:
        soe_run = evaluate_soe(
            industry_profile=request.industry_profile,
            inputs=request.inputs,
            hardware_class=request.hardware_class,
            additional_packs=request.additional_packs,
            active_profiles=request.active_profiles,  # Sprint 4
        )
        return soe_run
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SOE evaluation failed: {str(e)}",
        ) from e


class GenerateWhyRequest(BaseModel):
    """Request model for generating why explanation."""
    decision_id: str
    object_type: str
    object_id: str
    action: str
    enforcement: str
    why: Dict[str, Any]


@router.post("/explain")
def generate_why_endpoint(
    request: GenerateWhyRequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Generate human-readable 'why required' explanation for a decision."""
    from services.api.core.soe_engine import SOEDecision
    
    decision: SOEDecision = {
        "id": request.decision_id,
        "object_type": request.object_type,
        "object_id": request.object_id,
        "action": request.action,
        "enforcement": request.enforcement,
        "why": request.why,
    }
    
    try:
        explanation = generate_why_explanation(decision)
        return {
            "decision_id": request.decision_id,
            "explanation": explanation,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation generation failed: {str(e)}",
        ) from e


@router.post("/export-manifest")
def export_audit_manifest_endpoint(
    request: EvaluateSOERequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """
    Export audit manifest for an SOE evaluation.
    
    Returns comprehensive audit manifest with all rules, decisions, evidence, and citations.
    """
    try:
        soe_run = evaluate_soe(
            industry_profile=request.industry_profile,
            inputs=request.inputs,
            hardware_class=request.hardware_class,
            additional_packs=request.additional_packs,
            active_profiles=request.active_profiles,  # Sprint 4
        )
        
        manifest = export_audit_manifest(soe_run)
        return manifest
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Manifest export failed: {str(e)}",
        ) from e


@router.post("/decision-log")
def create_decision_log_endpoint(
    request: EvaluateSOERequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Create decision log with deterministic IDs and timestamps."""
    try:
        soe_run = evaluate_soe(
            industry_profile=request.industry_profile,
            inputs=request.inputs,
            hardware_class=request.hardware_class,
            additional_packs=request.additional_packs,
            active_profiles=request.active_profiles,  # Sprint 4
        )
        
        decision_log = create_decision_log(soe_run)
        return {
            "soe_version": soe_run["soe_version"],
            "industry_profile": soe_run["industry_profile"],
            "decision_count": len(decision_log),
            "decisions": decision_log,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decision log creation failed: {str(e)}",
        ) from e
