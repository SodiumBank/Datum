"""Datum Revision API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from services.api.core.deps import require_role
from services.api.core.revision_manager import (
    create_revision,
    get_revision,
    list_revisions,
    create_revision_for_update,
    check_locked,
)
from services.api.core.storage import get_lock

router = APIRouter()


class CreateRevisionRequest(BaseModel):
    """Request model for creating a revision."""
    org_id: str
    design_id: str
    reason: str


@router.post("")
def create_revision_endpoint(
    request: CreateRevisionRequest,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """
    Create a new DatumRevision.
    
    Revisions mark immutable snapshots of a design. Once created, they cannot be modified.
    """
    try:
        revision = create_revision(
            org_id=request.org_id,
            design_id=request.design_id,
            reason=request.reason,
            created_by=auth.get("sub", "unknown"),
        )
        return revision
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Revision creation failed: {str(e)}",
        ) from e


@router.get("/{revision_id}")
def get_revision_endpoint(
    revision_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Get a specific revision by ID."""
    revision = get_revision(revision_id)
    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revision not found: {revision_id}",
        )
    return revision


@router.get("")
def list_revisions_endpoint(
    org_id: str | None = None,
    design_id: str | None = None,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """List revisions, optionally filtered by org_id or design_id."""
    revisions = list_revisions(org_id=org_id, design_id=design_id)
    return {"revisions": revisions, "count": len(revisions)}


class CreateRevisionForUpdateRequest(BaseModel):
    """Request model for creating a revision when updating a locked entity."""
    org_id: str
    design_id: str
    entity_type: str
    entity_id: str
    reason: str


@router.post("/for-update")
def create_revision_for_update_endpoint(
    request: CreateRevisionForUpdateRequest,
    auth: dict = Depends(require_role("OPS", "ADMIN")),
):
    """
    Create a new revision when updating a locked entity.
    
    This endpoint checks if an entity is locked and creates a new revision if needed.
    """
    try:
        # Check if entity is locked
        if not check_locked(request.entity_type, request.entity_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{request.entity_type} {request.entity_id} is not locked. Update directly.",
            )
        
        revision = create_revision_for_update(
            org_id=request.org_id,
            design_id=request.design_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            reason=request.reason,
            created_by=auth.get("sub", "unknown"),
        )
        
        if revision:
            return {
                "revision": revision,
                "message": f"New revision created: {revision['id']}",
            }
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create revision",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Revision creation failed: {str(e)}",
        ) from e


@router.get("/entity/{entity_type}/{entity_id}/lock")
def check_entity_lock_endpoint(
    entity_type: str,
    entity_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN")),
):
    """Check if an entity is locked."""
    lock = get_lock(entity_type, entity_id)
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "locked": lock is not None,
        "lock": lock,
    }
