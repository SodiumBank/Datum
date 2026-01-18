"""SOE Audit & Transparency - Decision logging and manifest export."""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from services.api.core.soe_engine import SOERun, SOEDecision

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS = ROOT / "schemas"


def generate_deterministic_decision_id(
    rule_id: str,
    object_type: str,
    object_id: str,
    context: Dict[str, Any],
) -> str:
    """
    Generate deterministic decision ID from rule and context.
    
    Same rule + same context = same decision ID.
    """
    # Create deterministic string from inputs
    key_parts = [
        rule_id,
        object_type,
        object_id,
        str(context.get("industry_profile", "")),
        str(context.get("hardware_class", "")),
    ]
    key_string = "|".join(key_parts)
    
    # Generate hash
    hash_obj = hashlib.sha256(key_string.encode("utf-8"))
    hash_hex = hash_obj.hexdigest()[:8].upper()
    
    # Format as DEC-XXXX
    return f"DEC-{hash_hex}"


def export_audit_manifest(soe_run: SOERun) -> Dict[str, Any]:
    """
    Export audit manifest listing all rules, decisions, evidence, and citations.
    
    This manifest is audit-ready and can be exported for compliance documentation.
    """
    manifest = {
        "soe_version": soe_run["soe_version"],
        "industry_profile": soe_run["industry_profile"],
        "hardware_class": soe_run.get("hardware_class"),
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "active_packs": soe_run["active_packs"],
        "decisions": [],
        "rules_applied": [],
        "evidence_required": soe_run["required_evidence"],
        "gates": soe_run["gates"],
        "cost_modifiers": soe_run["cost_modifiers"],
    }
    
    # Enrich decisions with rule details
    for decision in soe_run["decisions"]:
        enriched_decision = {
            "id": decision["id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "object_type": decision["object_type"],
            "object_id": decision["object_id"],
            "action": decision["action"],
            "enforcement": decision["enforcement"],
            "rule_id": decision["why"]["rule_id"],
            "pack_id": decision["why"]["pack_id"],
            "citations": decision["why"].get("citations", []),
            "explanation": _generate_decision_explanation(decision),
        }
        manifest["decisions"].append(enriched_decision)
        
        # Collect unique rule references
        rule_ref = {
            "rule_id": decision["why"]["rule_id"],
            "pack_id": decision["why"]["pack_id"],
            "citations": decision["why"].get("citations", []),
        }
        if rule_ref not in manifest["rules_applied"]:
            manifest["rules_applied"].append(rule_ref)
    
    return manifest


def _generate_decision_explanation(decision: SOEDecision) -> str:
    """Generate human-readable explanation for a decision."""
    rule_id = decision["why"].get("rule_id", "UNKNOWN")
    pack_id = decision["why"].get("pack_id", "UNKNOWN")
    citations = decision["why"].get("citations", [])
    
    # Load rule for summary
    from services.api.core.soe_engine import _load_standards_pack
    
    try:
        pack = _load_standards_pack(pack_id)
        rules = pack.get("rules", [])
        for rule in rules:
            if rule.get("rule_id") == rule_id:
                why = rule.get("why", {})
                summary = why.get("summary", f"{decision['action']} required by rule {rule_id}")
                if citations:
                    citation_str = ", ".join(citations)
                    return f"{summary} ({citation_str})"
                return summary
    except Exception:
        pass
    
    # Fallback
    citation_str = ", ".join(citations) if citations else ""
    if citation_str:
        return f"{decision['action']} required by {rule_id} in pack {pack_id} ({citation_str})"
    return f"{decision['action']} required by {rule_id} in pack {pack_id}"


def create_decision_log(soe_run: SOERun) -> List[Dict[str, Any]]:
    """
    Create decision log with deterministic IDs and timestamps.
    
    Returns list of decision log entries.
    """
    decision_log = []
    
    for decision in soe_run["decisions"]:
        log_entry = {
            "decision_id": decision["id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule_id": decision["why"]["rule_id"],
            "pack_id": decision["why"]["pack_id"],
            "object_type": decision["object_type"],
            "object_id": decision["object_id"],
            "action": decision["action"],
            "enforcement": decision["enforcement"],
            "citations": decision["why"].get("citations", []),
        }
        decision_log.append(log_entry)
    
    return decision_log
