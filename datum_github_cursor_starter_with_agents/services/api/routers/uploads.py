import hashlib
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from services.api.core.deps import require_role
from services.api.core.storage import (
    save_gerber_zip,
    save_bom_file,
    generate_upload_id,
    save_normalized_bom,
    get_normalized_bom,
    save_board_metrics,
    get_board_metrics,
)
from services.api.core.bom_parser import parse_bom
from services.api.core.gerber_parser import extract_board_metrics
from services.api.core.schema_validation import validate_schema

router = APIRouter()

def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

@router.post("/gerbers")
async def upload_gerbers(
    file: UploadFile = File(...),
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN"))
):
    """
    Upload Gerber ZIP file and persist metadata per Datum Design Package schema.
    
    Returns gerber_set metadata with upload_id, sha256, files, and created_at.
    Files are extracted and cataloged by type (GERBER, EXCELLON, etc.).
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expected ZIP file for Gerber upload",
        )
    
    data = await file.read()
    upload_id = generate_upload_id("gerb")
    
    try:
        gerber_set = save_gerber_zip(upload_id, data, file.filename)
        
        # Extract board metrics from Gerber files
        try:
            metrics = extract_board_metrics(upload_id, gerber_set["files"])
            save_board_metrics(upload_id, metrics)
        except Exception as metrics_exc:
            # Don't fail upload if metrics extraction fails
            # Log error but continue
            print(f"Warning: Board metrics extraction failed for {upload_id}: {metrics_exc}")
        
        return gerber_set
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

@router.post("/bom")
async def upload_bom(
    file: UploadFile = File(...),
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN"))
):
    """
    Upload BOM file (CSV or XLSX), parse, normalize, and persist metadata.
    
    Returns BOM metadata with upload_id, sha256, format, created_at, and items.
    BOM is normalized and validated against Datum Design Package schema.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename required for BOM upload",
        )
    
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith((".csv", ".xlsx", ".xls"))):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expected CSV or XLSX file for BOM upload",
        )
    
    data = await file.read()
    upload_id = generate_upload_id("bom")
    
    try:
        # Save file and get metadata
        bom_metadata = save_bom_file(upload_id, data, file.filename)
        file_format = bom_metadata["format"]
        
        # Parse and normalize BOM
        items = parse_bom(data, file_format)
        
        # Save normalized BOM
        save_normalized_bom(upload_id, items)
        
        # Validate against schema (partial - just the items array structure)
        # Full validation happens when creating Design Package
        for item in items:
            # Basic validation - ensure required fields present
            if not item.get("refdes") or not item.get("qty") or not item.get("mpn"):
                raise ValueError("Normalized BOM item missing required fields")
        
        # Return metadata with items
        return {
            **bom_metadata,
            "items": items,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/bom/{upload_id}/normalized")
async def get_bom_normalized(
    upload_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN"))
):
    """
    Get normalized BOM items for a given upload_id.
    
    Returns list of normalized BOM items with refdes, qty, mpn, and optional fields.
    """
    items = get_normalized_bom(upload_id)
    if items is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Normalized BOM not found for upload_id: {upload_id}",
        )
    return {"upload_id": upload_id, "items": items}


@router.get("/gerbers/{upload_id}/metrics")
async def get_gerber_metrics(
    upload_id: str,
    auth: dict = Depends(require_role("CUSTOMER", "OPS", "ADMIN"))
):
    """
    Get board metrics extracted from Gerber files for a given upload_id.
    
    Returns board metrics with layer_count, dimensions, area, etc.
    Metrics are surfaced in quote inputs for pricing calculations.
    """
    metrics = get_board_metrics(upload_id)
    if metrics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board metrics not found for upload_id: {upload_id}",
        )
    return {"upload_id": upload_id, **metrics}
