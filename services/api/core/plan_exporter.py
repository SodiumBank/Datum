"""DatumPlan export engine - production-ready exports (Sprint 3-5).

SPRINT 3: Generate production-ready exports only from approved plans.
SPRINT 5: Export hardening (hash, provenance metadata, read-only enforcement).
"""

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from services.api.core.storage import get_plan, get_soe_run
from services.api.core.execution_outputs import generate_all_execution_outputs


def validate_plan_exportable(plan: Dict[str, Any], require_tier_3: bool = False) -> tuple[bool, str]:
    """
    Check if plan can be exported (Sprint 7: must be approved + optionally tier gated).
    
    Args:
        plan: Plan to validate
        require_tier_3: If True, requires quote.tier >= TIER_3 (Sprint 7: tier enforcement)
    
    Returns:
        (is_exportable, error_message)
    """
    if plan.get("state") != "approved":
        return (
            False,
            f"Plan is in {plan.get('state')} state. Only approved plans can be exported.",
        )
    
    if not plan.get("locked"):
        return (
            False,
            "Approved plans must be locked before export.",
        )
    
    # Sprint 7: Tier enforcement for Tier 3 exports
    if require_tier_3:
        quote_id = plan.get("quote_id")
        if not quote_id:
            return (
                False,
                "Plan missing quote_id - cannot verify tier.",
            )
        
        from services.api.core.storage import get_quote
        quote = get_quote(quote_id)
        if not quote:
            return (
                False,
                f"Quote {quote_id} not found - cannot verify tier.",
            )
        
        tier = quote.get("tier", "TIER_1")
        tier_order = {"TIER_1": 1, "TIER_2": 2, "TIER_3": 3}
        quote_tier_order = tier_order.get(tier, 1)
        
        if quote_tier_order < 3:
            return (
                False,
                f"Export requires Tier 3. Plan is Tier {tier}. Upgrade to Tier 3 to export.",
            )
    
    return (True, "")


def export_plan_to_csv(plan: Dict[str, Any]) -> str:
    """
    Export plan to CSV format (Sprint 3: production-ready).
    
    Returns:
        CSV string with plan steps and metadata
    """
    is_exportable, error_msg = validate_plan_exportable(plan)
    if not is_exportable:
        raise ValueError(error_msg)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["Plan Export", plan.get("id", ""), plan.get("plan_revision", ""), plan.get("version", 1)])
    writer.writerow([])
    
    # Steps
    writer.writerow(["Steps"])
    writer.writerow(["Sequence", "Type", "Title", "Required", "Locked", "SOE Decision ID"])
    
    for step in sorted(plan.get("steps", []), key=lambda s: s.get("sequence", 0)):
        writer.writerow([
            step.get("sequence"),
            step.get("type"),
            step.get("title"),
            step.get("required", False),
            step.get("locked_sequence", False),
            step.get("soe_decision_id", ""),
        ])
    
    writer.writerow([])
    
    # Tests
    writer.writerow(["Tests"])
    writer.writerow(["Test Type", "Title", "Required", "SOE Decision ID"])
    
    for test in plan.get("tests", []):
        writer.writerow([
            test.get("test_type"),
            test.get("title"),
            test.get("required", False),
            test.get("soe_decision_id", ""),
        ])
    
    return output.getvalue()


def export_plan_to_json(plan: Dict[str, Any], include_execution_outputs: bool = False, require_tier_3: bool = False) -> Dict[str, Any]:
    """
    Export plan to JSON format (Sprint 3: production-ready, Sprint 5: hardened, Sprint 7: tier-gated).
    
    Args:
        plan: Plan to export
        include_execution_outputs: Whether to include execution outputs
        require_tier_3: If True, requires Tier 3 (Sprint 7: tier enforcement)
    
    Returns:
        JSON-serializable dict with provenance metadata and hash
    """
    is_exportable, error_msg = validate_plan_exportable(plan, require_tier_3=require_tier_3)
    if not is_exportable:
        raise ValueError(error_msg)
    
    # Get SOERun for profile stack (Sprint 5: provenance metadata)
    profile_stack_metadata = None
    soe_run_id = plan.get("soe_run_id")
    if soe_run_id:
        soe_run = get_soe_run(soe_run_id)
        if soe_run:
            profile_stack_metadata = {
                "active_profiles": soe_run.get("active_profiles", []),
                "profile_stack": soe_run.get("profile_stack", []),
            }
    
    export = {
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "plan_id": plan.get("id"),
        "plan_revision": plan.get("plan_revision"),
        "version": plan.get("version"),
        "state": plan.get("state"),
        "quote_id": plan.get("quote_id"),
        "steps": plan.get("steps", []),
        "tests": plan.get("tests", []),
        "evidence_intent": plan.get("evidence_intent", []),
        "soe_run_id": plan.get("soe_run_id"),
        "soe_decision_ids": plan.get("soe_decision_ids", []),
        # Sprint 5: Provenance metadata
        "provenance": {
            "plan_version": plan.get("version"),
            "approved_by": plan.get("approved_by"),
            "approved_at": plan.get("approved_at"),
            "profile_stack": profile_stack_metadata,
            "export_generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    
    if include_execution_outputs:
        # Get execution outputs (requires upload_id from quote)
        from services.api.core.storage import get_quote
        quote = get_quote(plan.get("quote_id"))
        if quote:
            upload_id = quote.get("gerber_upload_id") or quote.get("inputs", {}).get("gerber_upload_id")
            if upload_id:
                from services.api.core.storage import get_normalized_bom
                bom_items = get_normalized_bom(upload_id)
                execution_outputs = generate_all_execution_outputs(upload_id, bom_items)
                export["execution_outputs"] = execution_outputs
    
    # Sprint 5: Generate hash for export integrity
    export_json_str = json.dumps(export, sort_keys=True, ensure_ascii=False)
    export_hash = hashlib.sha256(export_json_str.encode("utf-8")).hexdigest()
    export["provenance"]["export_hash"] = export_hash
    
    return export


def export_placement_csv(
    plan: Dict[str, Any],
    placement_output: Dict[str, Any],
) -> str:
    """
    Export placement data to CSV (machine-readable format).
    
    Returns:
        CSV string in XYRS format
    """
    is_exportable, error_msg = validate_plan_exportable(plan)
    if not is_exportable:
        raise ValueError(error_msg)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["# XYRS Placement File"])
    writer.writerow(["# Generated from DatumPlan", plan.get("id", "")])
    writer.writerow(["# Format: RefDes, X(mm), Y(mm), Rotation(deg), Side"])
    writer.writerow([])
    
    # Placements
    writer.writerow(["RefDes", "X", "Y", "Rotation", "Side"])
    
    for placement in placement_output.get("placements", []):
        writer.writerow([
            placement.get("refdes"),
            placement.get("x_mm", 0),
            placement.get("y_mm", 0),
            placement.get("rotation_deg", 0),
            placement.get("side", "TOP"),
        ])
    
    return output.getvalue()
