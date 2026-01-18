"""File storage service for Datum uploads."""

import hashlib
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import secrets
import string

ROOT = Path(__file__).resolve().parents[3]
STORAGE_DIR = Path(os.getenv("DATUM_STORAGE_DIR", str(ROOT / "storage")))
UPLOADS_DIR = STORAGE_DIR / "uploads"

# Lazy directory creation - create when needed
def _ensure_storage_dirs():
    """Ensure storage directories exist."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _sha256_bytes(b: bytes) -> str:
    """Compute SHA256 hash of bytes."""
    return hashlib.sha256(b).hexdigest()


def generate_upload_id(prefix: str = "upl") -> str:
    """Generate a unique upload ID."""
    random_suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    return f"{prefix}_{random_suffix}"


def _detect_gerber_file_type(filename: str) -> Literal["GERBER", "EXCELLON", "READ_ME", "STACKUP", "DRAWING", "OTHER"]:
    """Detect file type from filename extension."""
    filename_lower = filename.lower()
    if filename_lower.endswith((".gbr", ".art", ".pho", ".ger")):
        return "GERBER"
    elif filename_lower.endswith((".drl", ".drill", ".txt")) and "drill" in filename_lower:
        return "EXCELLON"
    elif filename_lower.endswith((".readme", ".txt", ".md")) and ("read" in filename_lower or "note" in filename_lower):
        return "READ_ME"
    elif filename_lower.endswith((".stackup", ".stack")):
        return "STACKUP"
    elif filename_lower.endswith((".pdf", ".dwg", ".dxf")):
        return "DRAWING"
    else:
        return "OTHER"


def save_gerber_zip(upload_id: str, zip_data: bytes, filename: str | None) -> dict:
    _ensure_storage_dirs()
    """
    Save Gerber ZIP file and extract metadata.
    
    Returns dict with:
    - upload_id: str
    - sha256: str
    - files: list[dict] with path and type
    - created_at: str (ISO timestamp)
    """
    sha256_hash = _sha256_bytes(zip_data)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Save ZIP file
    zip_path = UPLOADS_DIR / f"{upload_id}.zip"
    zip_path.write_bytes(zip_data)
    
    # Extract and catalog files
    files = []
    extract_dir = UPLOADS_DIR / upload_id
    extract_dir.mkdir(exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for member in zip_ref.namelist():
                # Skip directories
                if member.endswith("/"):
                    continue
                
                # Extract file
                file_path = extract_dir / member
                file_path.parent.mkdir(parents=True, exist_ok=True)
                zip_ref.extract(member, extract_dir)
                
                # Detect file type
                file_type = _detect_gerber_file_type(member)
                
                # Store relative path from upload directory
                rel_path = f"{upload_id}/{member}"
                files.append({"path": rel_path, "type": file_type})
    except zipfile.BadZipFile:
        raise ValueError("Invalid ZIP file")
    
    gerber_set = {
        "upload_id": upload_id,
        "sha256": sha256_hash,
        "files": files,
        "created_at": timestamp,
    }
    
    # Save metadata for later retrieval
    save_gerber_set_metadata(upload_id, gerber_set)
    
    return gerber_set


def save_bom_file(upload_id: str, bom_data: bytes, filename: str | None) -> dict:
    _ensure_storage_dirs()
    """
    Save BOM file.
    
    Returns dict with:
    - upload_id: str
    - sha256: str
    - format: "CSV" or "XLSX"
    - created_at: str (ISO timestamp)
    """
    sha256_hash = _sha256_bytes(bom_data)
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Detect format
    filename_lower = (filename or "").lower()
    if filename_lower.endswith((".xlsx", ".xls")):
        file_format = "XLSX"
        file_path = UPLOADS_DIR / f"{upload_id}.xlsx"
    else:
        file_format = "CSV"
        file_path = UPLOADS_DIR / f"{upload_id}.csv"
    
    # Save file
    file_path.write_bytes(bom_data)
    
    return {
        "upload_id": upload_id,
        "sha256": sha256_hash,
        "format": file_format,
        "created_at": timestamp,
    }


def save_normalized_bom(upload_id: str, items: list[dict]) -> None:
    """Save normalized BOM items as JSON."""
    bom_json_path = UPLOADS_DIR / f"{upload_id}_normalized.json"
    bom_json_path.write_text(json.dumps(items, indent=2), encoding="utf-8")


def get_normalized_bom(upload_id: str) -> list[dict] | None:
    """Get normalized BOM items from JSON."""
    bom_json_path = UPLOADS_DIR / f"{upload_id}_normalized.json"
    if not bom_json_path.exists():
        return None
    return json.loads(bom_json_path.read_text(encoding="utf-8"))


def save_board_metrics(upload_id: str, metrics: dict) -> None:
    """Save board metrics as JSON."""
    metrics_path = UPLOADS_DIR / f"{upload_id}_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


def get_board_metrics(upload_id: str) -> dict | None:
    """Get board metrics from JSON."""
    metrics_path = UPLOADS_DIR / f"{upload_id}_metrics.json"
    if not metrics_path.exists():
        return None
    return json.loads(metrics_path.read_text(encoding="utf-8"))


def get_gerber_files(upload_id: str) -> list[dict] | None:
    """Get Gerber files list for an upload_id."""
    # Try to load from saved metadata (we should save it, but for now reconstruct)
    # Check if we have a saved gerber_set metadata
    gerber_set_path = UPLOADS_DIR / f"{upload_id}_gerber_set.json"
    if gerber_set_path.exists():
        data = json.loads(gerber_set_path.read_text(encoding="utf-8"))
        return data.get("files", [])
    
    # Fallback: reconstruct from upload directory
    upload_dir = UPLOADS_DIR / upload_id
    if not upload_dir.exists():
        return None
    
    files = []
    for file_path in upload_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(upload_dir)
            file_type = _detect_gerber_file_type(str(rel_path))
            files.append({
                "path": f"{upload_id}/{rel_path}",
                "type": file_type,
            })
    
    return files if files else None


def save_gerber_set_metadata(upload_id: str, gerber_set: dict) -> None:
    """Save Gerber set metadata for later retrieval."""
    metadata_path = UPLOADS_DIR / f"{upload_id}_gerber_set.json"
    metadata_path.write_text(json.dumps(gerber_set, indent=2), encoding="utf-8")


# Quote storage
QUOTES_DIR = STORAGE_DIR / "quotes"
LOCKS_DIR = STORAGE_DIR / "locks"
AUDIT_DIR = STORAGE_DIR / "audit"


def save_quote(quote: dict) -> None:
    """Save quote to storage."""
    _ensure_storage_dirs()
    QUOTES_DIR.mkdir(parents=True, exist_ok=True)
    quote_id = quote["id"]
    quote_path = QUOTES_DIR / f"{quote_id}.json"
    quote_path.write_text(json.dumps(quote, indent=2), encoding="utf-8")


def get_quote(quote_id: str) -> dict | None:
    """Get quote from storage."""
    quote_path = QUOTES_DIR / f"{quote_id}.json"
    if not quote_path.exists():
        return None
    return json.loads(quote_path.read_text(encoding="utf-8"))


def list_quotes(status_filter: str | None = None) -> list[dict]:
    """List all quotes, optionally filtered by status."""
    _ensure_storage_dirs()
    if not QUOTES_DIR.exists():
        return []
    
    quotes = []
    for quote_file in QUOTES_DIR.glob("*.json"):
        try:
            quote = json.loads(quote_file.read_text(encoding="utf-8"))
            if status_filter is None or quote.get("status") == status_filter:
                quotes.append(quote)
        except Exception:
            continue
    
    # Sort by created_at descending
    quotes.sort(key=lambda q: q.get("created_at", ""), reverse=True)
    return quotes


def save_lock(lock: dict) -> None:
    """Save lock to storage."""
    _ensure_storage_dirs()
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)
    lock_id = lock["id"]
    lock_path = LOCKS_DIR / f"{lock_id}.json"
    lock_path.write_text(json.dumps(lock, indent=2), encoding="utf-8")


def get_lock(entity_type: str, entity_id: str) -> dict | None:
    """Get lock for an entity."""
    if not LOCKS_DIR.exists():
        return None
    
    # Search for lock by entity
    for lock_file in LOCKS_DIR.glob("*.json"):
        try:
            lock = json.loads(lock_file.read_text(encoding="utf-8"))
            if lock.get("entity_type") == entity_type and lock.get("entity_id") == entity_id:
                return lock
        except Exception:
            continue
    
    return None


def save_audit_event(event: dict) -> None:
    """Save audit event to storage."""
    _ensure_storage_dirs()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    event_id = event["id"]
    event_path = AUDIT_DIR / f"{event_id}.json"
    event_path.write_text(json.dumps(event, indent=2), encoding="utf-8")


def list_audit_events(entity_type: str | None = None, entity_id: str | None = None) -> list[dict]:
    """List audit events, optionally filtered by entity."""
    _ensure_storage_dirs()
    if not AUDIT_DIR.exists():
        return []
    
    events = []
    for event_file in AUDIT_DIR.glob("*.json"):
        try:
            event = json.loads(event_file.read_text(encoding="utf-8"))
            if entity_type and event.get("entity_type") != entity_type:
                continue
            if entity_id and event.get("entity_id") != entity_id:
                continue
            events.append(event)
        except Exception:
            continue
    
    # Sort by timestamp descending
    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return events


# Plan storage
PLANS_DIR = STORAGE_DIR / "plans"


def save_plan(plan: dict) -> None:
    """Save plan to storage."""
    _ensure_storage_dirs()
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    plan_id = plan["id"]
    plan_path = PLANS_DIR / f"{plan_id}.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")


def get_plan(plan_id: str) -> dict | None:
    """Get plan from storage."""
    plan_path = PLANS_DIR / f"{plan_id}.json"
    if not plan_path.exists():
        return None
    return json.loads(plan_path.read_text(encoding="utf-8"))


def list_plans(quote_id: str | None = None) -> list[dict]:
    """List plans, optionally filtered by quote_id."""
    _ensure_storage_dirs()
    if not PLANS_DIR.exists():
        return []
    
    plans = []
    for plan_file in PLANS_DIR.glob("*.json"):
        try:
            plan = json.loads(plan_file.read_text(encoding="utf-8"))
            if quote_id and plan.get("quote_id") != quote_id:
                continue
            plans.append(plan)
        except Exception:
            continue
    
    # Sort by created_at descending
    plans.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    return plans


# Tests storage
TESTS_DIR = STORAGE_DIR / "tests"


def save_tests(tests: dict) -> None:
    """Save tests to storage."""
    _ensure_storage_dirs()
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    tests_id = tests["id"]
    tests_path = TESTS_DIR / f"{tests_id}.json"
    tests_path.write_text(json.dumps(tests, indent=2), encoding="utf-8")


def get_tests(tests_id: str) -> dict | None:
    """Get tests from storage."""
    tests_path = TESTS_DIR / f"{tests_id}.json"
    if not tests_path.exists():
        return None
    return json.loads(tests_path.read_text(encoding="utf-8"))


def list_tests(plan_id: str | None = None) -> list[dict]:
    """List tests, optionally filtered by plan_id."""
    _ensure_storage_dirs()
    if not TESTS_DIR.exists():
        return []
    
    tests_list = []
    for tests_file in TESTS_DIR.glob("*.json"):
        try:
            tests = json.loads(tests_file.read_text(encoding="utf-8"))
            if plan_id and tests.get("plan_id") != plan_id:
                continue
            tests_list.append(tests)
        except Exception:
            continue
    
    # Sort by plan_revision descending
    tests_list.sort(key=lambda t: t.get("plan_revision", ""), reverse=True)
    return tests_list


# Revision storage
REVISIONS_DIR = STORAGE_DIR / "revisions"


def save_revision(revision: dict) -> None:
    """Save revision to storage."""
    _ensure_storage_dirs()
    REVISIONS_DIR.mkdir(parents=True, exist_ok=True)
    revision_id = revision["id"]
    revision_path = REVISIONS_DIR / f"{revision_id}.json"
    revision_path.write_text(json.dumps(revision, indent=2), encoding="utf-8")


def get_revision(revision_id: str) -> dict | None:
    """Get revision from storage."""
    revision_path = REVISIONS_DIR / f"{revision_id}.json"
    if not revision_path.exists():
        return None
    return json.loads(revision_path.read_text(encoding="utf-8"))


def list_revisions(org_id: str | None = None, design_id: str | None = None) -> list[dict]:
    """List revisions, optionally filtered by org_id or design_id."""
    _ensure_storage_dirs()
    if not REVISIONS_DIR.exists():
        return []
    
    revisions = []
    for revision_file in REVISIONS_DIR.glob("*.json"):
        try:
            revision = json.loads(revision_file.read_text(encoding="utf-8"))
            if org_id and revision.get("org_id") != org_id:
                continue
            if design_id and revision.get("design_id") != design_id:
                continue
            revisions.append(revision)
        except Exception:
            continue
    
    # Sort by created_at descending
    revisions.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return revisions


# SOERun storage
SOE_RUNS_DIR = STORAGE_DIR / "soe_runs"


def save_soe_run(soe_run: dict) -> None:
    """Save SOERun to storage."""
    _ensure_storage_dirs()
    SOE_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    # Use a deterministic key based on inputs
    import hashlib
    import json
    key_data = {
        "industry_profile": soe_run.get("industry_profile"),
        "hardware_class": soe_run.get("hardware_class"),
        "inputs": soe_run.get("inputs"),
    }
    key_str = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.sha256(key_str.encode("utf-8")).hexdigest()[:16]
    soe_run_path = SOE_RUNS_DIR / f"{key_hash}.json"
    soe_run_path.write_text(json.dumps(soe_run, indent=2), encoding="utf-8")


def get_soe_run(project_id: str | None = None, quote_id: str | None = None) -> dict | None:
    """Get SOERun by project_id or quote_id (if linked)."""
    _ensure_storage_dirs()
    if not SOE_RUNS_DIR.exists():
        return None
    
    # For now, return most recent if no ID provided
    # In future, link SOERun to project/quote via metadata
    if project_id or quote_id:
        # Search for SOERun linked to project/quote
        for soe_file in SOE_RUNS_DIR.glob("*.json"):
            try:
                soe_run = json.loads(soe_file.read_text(encoding="utf-8"))
                metadata = soe_run.get("metadata", {})
                if metadata.get("project_id") == project_id or metadata.get("quote_id") == quote_id:
                    return soe_run
            except Exception:
                continue
        return None
    
    # Return most recent
    soe_runs = []
    for soe_file in SOE_RUNS_DIR.glob("*.json"):
        try:
            soe_run = json.loads(soe_file.read_text(encoding="utf-8"))
            soe_runs.append(soe_run)
        except Exception:
            continue
    
    if soe_runs:
        # Sort by timestamp if available
        soe_runs.sort(key=lambda r: r.get("evaluation_timestamp", ""), reverse=True)
        return soe_runs[0]
    
    return None


def get_upload_path(upload_id: str, filename: str | None = None) -> Path | None:
    """Get path to stored upload file."""
    if filename:
        # Try to find specific file in extracted directory
        upload_dir = UPLOADS_DIR / upload_id
        if upload_dir.exists():
            file_path = upload_dir / filename
            if file_path.exists():
                return file_path
    
    # Try ZIP file
    zip_path = UPLOADS_DIR / f"{upload_id}.zip"
    if zip_path.exists():
        return zip_path
    
    # Try CSV/XLSX
    csv_path = UPLOADS_DIR / f"{upload_id}.csv"
    if csv_path.exists():
        return csv_path
    
    xlsx_path = UPLOADS_DIR / f"{upload_id}.xlsx"
    if xlsx_path.exists():
        return xlsx_path
    
    return None
