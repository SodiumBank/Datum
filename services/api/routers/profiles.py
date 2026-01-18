"""Standards Profile Lifecycle API endpoints (Sprint 5)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from services.api.core.deps import require_role
from services.api.core.profile_lifecycle import (
    get_profile_state,
    submit_profile_for_approval,
    approve_profile,
    reject_profile,
    deprecate_profile,
    can_modify_profile,
    validate_profile_for_use,
)
from services.api.core.profile_stack import load_profile

router = APIRouter()


class SubmitProfileRequest(BaseModel):
    """Request model for submitting profile."""
    reason: str | None = None


class ApproveProfileRequest(BaseModel):
    """Request model for approving profile."""
    reason: str | None = None


class RejectProfileRequest(BaseModel):
    """Request model for rejecting profile."""
    reason: str  # Required


class DeprecateProfileRequest(BaseModel):
    """Request model for deprecating profile."""
    reason: str  # Required
    superseded_by: str | None = None


@router.get("/profiles/{profile_id}/state")
def get_profile_state_endpoint(
    profile_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Get current state of a profile."""
    try:
        state = get_profile_state(profile_id)
        profile = load_profile(profile_id)
        metadata = profile.get("metadata", {})
        return {
            "profile_id": profile_id,
            "state": state,
            "state_updated_at": metadata.get("state_updated_at"),
            "state_updated_by": metadata.get("state_updated_by"),
            "state_reason": metadata.get("state_reason"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile state: {str(e)}",
        ) from e


@router.post("/profiles/{profile_id}/submit")
def submit_profile_endpoint(
    profile_id: str,
    request: SubmitProfileRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Submit profile for approval (draft → submitted)."""
    try:
        user_id = auth.get("user_id", "system")
        profile = submit_profile_for_approval(profile_id, user_id, request.reason)
        return {
            "profile_id": profile_id,
            "state": "submitted",
            "profile": profile,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit profile: {str(e)}",
        ) from e


@router.post("/profiles/{profile_id}/approve")
def approve_profile_endpoint(
    profile_id: str,
    request: ApproveProfileRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Approve profile (submitted → approved)."""
    try:
        user_id = auth.get("user_id", "system")
        profile = approve_profile(profile_id, user_id, request.reason)
        return {
            "profile_id": profile_id,
            "state": "approved",
            "profile": profile,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve profile: {str(e)}",
        ) from e


@router.post("/profiles/{profile_id}/reject")
def reject_profile_endpoint(
    profile_id: str,
    request: RejectProfileRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Reject profile (submitted → draft)."""
    try:
        user_id = auth.get("user_id", "system")
        profile = reject_profile(profile_id, user_id, request.reason)
        return {
            "profile_id": profile_id,
            "state": "draft",
            "profile": profile,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject profile: {str(e)}",
        ) from e


@router.post("/profiles/{profile_id}/deprecate")
def deprecate_profile_endpoint(
    profile_id: str,
    request: DeprecateProfileRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Deprecate profile (approved → deprecated)."""
    try:
        user_id = auth.get("user_id", "system")
        profile = deprecate_profile(profile_id, user_id, request.reason, request.superseded_by)
        return {
            "profile_id": profile_id,
            "state": "deprecated",
            "profile": profile,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deprecate profile: {str(e)}",
        ) from e


@router.get("/profiles/{profile_id}/validate")
def validate_profile_endpoint(
    profile_id: str,
    allow_draft: bool = False,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Validate profile can be used in SOE runs or plans (Sprint 5: red-team guard)."""
    try:
        is_valid, error_msg = validate_profile_for_use(profile_id, allow_draft=allow_draft)
        return {
            "profile_id": profile_id,
            "is_valid": is_valid,
            "error_message": error_msg if not is_valid else None,
            "can_modify": can_modify_profile(profile_id),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate profile: {str(e)}",
        ) from e
