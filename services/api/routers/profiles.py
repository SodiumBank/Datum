"""Standards Profile Lifecycle, Versioning, and Bundles API (Sprint 5)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any, Dict, List

from services.api.core.deps import require_role
from services.api.core.profile_lifecycle import (
    get_profile_state,
    submit_profile_for_approval,
    approve_profile,
    reject_profile,
    deprecate_profile,
    validate_profile_for_use,
)
from services.api.core.profile_versioning import (
    create_profile_version,
    load_profile_version,
    list_profile_versions,
    compare_profile_versions,
)
from services.api.core.profile_bundles import (
    save_profile_bundle,
    load_profile_bundle,
    list_profile_bundles,
)

router = APIRouter()


class SubmitProfileRequest(BaseModel):
    """Request model for submitting profile."""
    reason: str | None = None


class ApproveProfileRequest(BaseModel):
    """Request model for approving profile."""
    reason: str | None = None


class RejectProfileRequest(BaseModel):
    """Request model for rejecting profile."""
    reason: str


class DeprecateProfileRequest(BaseModel):
    """Request model for deprecating profile."""
    reason: str
    superseded_by: str | None = None


class CreateProfileVersionRequest(BaseModel):
    """Request model for creating profile version."""
    new_version: str
    parent_version: str | None = None


@router.get("/{profile_id}/state")
def get_profile_state_endpoint(
    profile_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Get current state of a profile."""
    try:
        state = get_profile_state(profile_id)
        return {"profile_id": profile_id, "state": state}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/{profile_id}/submit")
def submit_profile_endpoint(
    profile_id: str,
    request: SubmitProfileRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Submit profile for approval (draft → submitted)."""
    try:
        user_id = auth.get("user_id", "system")
        profile = submit_profile_for_approval(profile_id, user_id, request.reason)
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/{profile_id}/approve")
def approve_profile_endpoint(
    profile_id: str,
    request: ApproveProfileRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Approve profile (submitted → approved)."""
    try:
        user_id = auth.get("user_id", "system")
        profile = approve_profile(profile_id, user_id, request.reason)
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/{profile_id}/reject")
def reject_profile_endpoint(
    profile_id: str,
    request: RejectProfileRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Reject profile (submitted → draft)."""
    try:
        user_id = auth.get("user_id", "system")
        profile = reject_profile(profile_id, user_id, request.reason)
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/{profile_id}/deprecate")
def deprecate_profile_endpoint(
    profile_id: str,
    request: DeprecateProfileRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Deprecate profile (approved → deprecated)."""
    try:
        user_id = auth.get("user_id", "system")
        profile = deprecate_profile(profile_id, user_id, request.reason, request.superseded_by)
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/{profile_id}/validate")
def validate_profile_endpoint(
    profile_id: str,
    allow_draft: bool = False,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Validate profile can be used in SOE runs or plans."""
    try:
        is_valid, error_msg = validate_profile_for_use(profile_id, allow_draft=allow_draft)
        return {
            "profile_id": profile_id,
            "is_valid": is_valid,
            "error_message": error_msg if not is_valid else None,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post("/{profile_id}/versions")
def create_profile_version_endpoint(
    profile_id: str,
    request: CreateProfileVersionRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Create a new version of a profile."""
    try:
        profile = create_profile_version(profile_id, request.new_version, request.parent_version)
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{profile_id}/versions")
def list_profile_versions_endpoint(
    profile_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """List all versions of a profile."""
    try:
        versions = list_profile_versions(profile_id)
        return {"profile_id": profile_id, "versions": versions}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/{profile_id}/versions/{version}")
def get_profile_version_endpoint(
    profile_id: str,
    version: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Get a specific version of a profile."""
    try:
        profile = load_profile_version(profile_id, version)
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/{profile_id}/versions/compare")
def compare_profile_versions_endpoint(
    profile_id: str,
    version1: str,
    version2: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Compare two profile versions."""
    try:
        diff = compare_profile_versions(profile_id, version1, version2)
        return diff
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/bundles")
def create_profile_bundle_endpoint(
    bundle: Dict[str, Any],
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """Create a profile bundle."""
    try:
        save_profile_bundle(bundle)
        return {"bundle_id": bundle.get("bundle_id"), "status": "created"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/bundles/{bundle_id}")
def get_profile_bundle_endpoint(
    bundle_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Get a profile bundle."""
    try:
        bundle = load_profile_bundle(bundle_id)
        return bundle
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get("/bundles")
def list_profile_bundles_endpoint(
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """List all profile bundles."""
    bundles = list_profile_bundles()
    return {"bundles": bundles}
