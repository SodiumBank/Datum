"""Datum Tests API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any

from services.api.core.deps import require_role
from services.api.core.tests_generator import generate_tests
from services.api.core.storage import get_tests, list_tests, save_audit_event
import secrets
import string
from datetime import datetime, timezone

router = APIRouter()


def _generate_id(prefix: str = "audit") -> str:
    """Generate a unique ID."""
    random_suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    return f"{prefix}_{random_suffix}"


class GenerateTestsRequest(BaseModel):
    """Request model for generating tests."""
    plan_id: str
    ruleset_version: int | None = None


@router.post("/generate")
def generate_tests_endpoint(
    request: GenerateTestsRequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """
    Generate DatumTests from a plan and ruleset.
    
    Returns declared tests with source_rules linked to plan revision.
    """
    try:
        tests = generate_tests(
            plan_id=request.plan_id,
            ruleset_version=request.ruleset_version,
        )
        
        # Create audit event
        timestamp = datetime.now(timezone.utc).isoformat()
        audit_event = {
            "id": _generate_id("audit"),
            "entity_type": "DATUM_TESTS",
            "entity_id": tests["id"],
            "action": "CREATE",
            "user_id": auth.get("sub", "unknown"),
            "timestamp": timestamp,
            "reason": f"Tests generated from plan {request.plan_id}",
        }
        save_audit_event(audit_event)
        
        return tests
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tests generation failed: {str(e)}",
        ) from e


@router.get("/{tests_id}")
def get_tests_endpoint(
    tests_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Get a specific tests declaration by ID."""
    tests = get_tests(tests_id)
    if not tests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tests not found: {tests_id}",
        )
    return tests


@router.get("")
def list_tests_endpoint(
    plan_id: str | None = None,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """List tests, optionally filtered by plan_id."""
    tests_list = list_tests(plan_id=plan_id)
    return {"tests": tests_list, "count": len(tests_list)}
