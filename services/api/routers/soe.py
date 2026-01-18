"""Standards Overlay Engine (SOE) API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any, Dict, List

from services.api.core.deps import require_role
from services.api.core.soe_engine import evaluate_soe, generate_why_explanation
from services.api.core.soe_audit import export_audit_manifest, create_decision_log

router = APIRouter()


class EvaluateSOERequest(BaseModel):
    """Request model for evaluating SOE (Sprint 4-5: supports active_profiles and bundles)."""
    industry_profile: str
    hardware_class: str | None = None
    inputs: Dict[str, Any]
    additional_packs: List[str] | None = None
    active_profiles: List[str] | None = None  # Sprint 4: Profile stack (BASE/DOMAIN/CUSTOMER_OVERRIDE)
    profile_bundle_id: str | None = None  # Sprint 5: Bundle selection (resolves to profile list)


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
            profile_bundle_id=request.profile_bundle_id,  # Sprint 5
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
    """Request model for generating why explanations."""
    decision_id: str
    soe_run: Dict[str, Any]


@router.post("/explain")
def generate_why_endpoint(
    request: GenerateWhyRequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """
    Generate human-readable explanation for an SOE decision.
    
    Returns why this decision was made, which rule triggered it, and citations.
    """
    try:
        # Find decision in SOERun
        decision = next(
            (d for d in request.soe_run.get("decisions", []) if d.get("id") == request.decision_id),
            None
        )
        if not decision:
            raise ValueError(f"Decision not found: {request.decision_id}")
        
        explanation = generate_why_explanation(decision)
        return {
            "decision_id": request.decision_id,
            "explanation": explanation,
            "why": decision.get("why", {}),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}",
        ) from e


@router.post("/export-manifest")
def export_audit_manifest_endpoint(
    request: EvaluateSOERequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """
    Export audit manifest for an SOE run.
    
    Returns audit-ready manifest with all rules, decisions, evidence, and citations.
    """
    try:
        soe_run = evaluate_soe(
            industry_profile=request.industry_profile,
            inputs=request.inputs,
            hardware_class=request.hardware_class,
            additional_packs=request.additional_packs,
            active_profiles=request.active_profiles,  # Sprint 4
            profile_bundle_id=request.profile_bundle_id,  # Sprint 5
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
            detail=f"Failed to export audit manifest: {str(e)}",
        ) from e


@router.post("/decision-log")
def create_decision_log_endpoint(
    request: EvaluateSOERequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """
    Create decision log for an SOE run.
    
    Returns log of all decisions with deterministic IDs and timestamps.
    """
    try:
        soe_run = evaluate_soe(
            industry_profile=request.industry_profile,
            inputs=request.inputs,
            hardware_class=request.hardware_class,
            additional_packs=request.additional_packs,
            active_profiles=request.active_profiles,  # Sprint 4
            profile_bundle_id=request.profile_bundle_id,  # Sprint 5
        )
        log = create_decision_log(soe_run)
        return log
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create decision log: {str(e)}",
        ) from e
