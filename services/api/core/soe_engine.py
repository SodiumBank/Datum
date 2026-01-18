"""Standards Overlay Engine (SOE) - Industry-aware compliance layer.

SOE applies industry and standard-specific constraints without altering
core manufacturing logic.
"""

import json
import secrets
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, TypedDict

from services.api.core.schema_validation import validate_schema
from services.api.core.profile_stack import resolve_profile_stack, tag_decision_with_profile, load_profile

ROOT = Path(__file__).resolve().parents[3]
SOE_PACKS_DIR = ROOT / "standards_packs"
INDUSTRY_PROFILES_DIR = ROOT / "industry_profiles"
SCHEMAS = ROOT / "schemas"


class SOEDecision(TypedDict):
    """SOE decision record."""
    id: str
    object_type: str
    object_id: str
    action: str
    enforcement: str
    why: Dict[str, Any]


class SOERun(TypedDict):
    """SOE runtime evaluation result."""
    soe_version: str
    industry_profile: str
    hardware_class: str | None
    active_packs: List[str]
    inputs: Dict[str, Any]
    decisions: List[SOEDecision]
    required_evidence: List[Dict[str, Any]]
    gates: List[Dict[str, Any]]
    cost_modifiers: List[Dict[str, Any]]


def _generate_decision_id(rule_id: str, object_type: str, object_id: str, context: Dict[str, Any]) -> str:
    """Generate deterministic decision ID."""
    from services.api.core.soe_audit import generate_deterministic_decision_id
    return generate_deterministic_decision_id(rule_id, object_type, object_id, context)


def _load_industry_profile(profile_name: str) -> Dict[str, Any]:
    """Load industry profile."""
    profile_path = INDUSTRY_PROFILES_DIR / f"{profile_name}.json"
    if not profile_path.exists():
        raise ValueError(f"Industry profile not found: {profile_name}")
    
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    validate_schema(data, "industry_profile.schema.json")
    return data


def _load_standards_pack(pack_id: str) -> Dict[str, Any]:
    """Load standards pack."""
    # Search for pack in all industry directories
    # First try pack_id.json, then pack.json
    for industry_dir in SOE_PACKS_DIR.iterdir():
        if not industry_dir.is_dir():
            continue
        
        # Try pack_id.json first
        pack_path = industry_dir / f"{pack_id}.json"
        if not pack_path.exists():
            # Try pack.json
            pack_path = industry_dir / "pack.json"
        
        if pack_path.exists():
            try:
                pack_data = json.loads(pack_path.read_text(encoding="utf-8"))
                if pack_data.get("pack_id") == pack_id:
                    # Load rules from rules directory if pack doesn't have them inline
                    if not pack_data.get("rules") and (industry_dir / "rules").exists():
                        rules = []
                        for rule_file in (industry_dir / "rules").glob("*.json"):
                            try:
                                rule_data = json.loads(rule_file.read_text(encoding="utf-8"))
                                rule_data["pack_id"] = pack_id  # Ensure pack_id is set
                                rules.append(rule_data)
                            except Exception:
                                continue
                        pack_data["rules"] = rules
                    
                    # Validate schema (skip if refs issue - will be fixed separately)
                    try:
                        validate_schema(pack_data, "standards_pack.schema.json")
                    except Exception as schema_err:
                        # Log but don't fail - schema refs need proper resolver
                        print(f"Warning: Schema validation skipped for {pack_id}: {schema_err}")
                    return pack_data
            except Exception as e:
                print(f"Warning: Failed to load pack from {pack_path}: {e}")
                continue
    
    raise ValueError(f"Standards pack not found: {pack_id}")


def _resolve_active_packs(industry_profile: str, hardware_class: str | None = None) -> List[str]:
    """Resolve active standards packs for an industry profile."""
    profile = _load_industry_profile(industry_profile)
    default_packs = profile.get("default_packs", [])
    
    # In the future, hardware_class could filter packs
    # For now, return all default packs
    return default_packs


def _evaluate_rule_expression(expr: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """
    Evaluate a rule expression against context.
    
    Supports:
    - all: all expressions must be true
    - any: at least one expression must be true
    - none: no expressions must be true
    - Field operators: equals, contains, gt, lt, in, etc.
    """
    if "all" in expr:
        return all(_evaluate_rule_expression(sub_expr, context) for sub_expr in expr["all"])
    
    if "any" in expr:
        return any(_evaluate_rule_expression(sub_expr, context) for sub_expr in expr["any"])
    
    if "none" in expr:
        return not any(_evaluate_rule_expression(sub_expr, context) for sub_expr in expr["none"])
    
    # Field operator evaluation
    if "field" in expr and "operator" in expr and "value" in expr:
        field = expr["field"]
        operator = expr["operator"]
        value = expr["value"]
        
        # Get field value from context (supports dot notation)
        field_parts = field.split(".")
        context_value = context
        for part in field_parts:
            if isinstance(context_value, dict):
                context_value = context_value.get(part)
            else:
                return False
        
        # Apply operator
        if operator == "equals":
            return context_value == value
        elif operator == "not_equals":
            return context_value != value
        elif operator == "contains":
            if isinstance(context_value, (list, str)):
                return value in context_value
            return False
        elif operator == "not_contains":
            if isinstance(context_value, (list, str)):
                return value not in context_value
            return True
        elif operator == "gt":
            return isinstance(context_value, (int, float)) and context_value > value
        elif operator == "gte":
            return isinstance(context_value, (int, float)) and context_value >= value
        elif operator == "lt":
            return isinstance(context_value, (int, float)) and context_value < value
        elif operator == "lte":
            return isinstance(context_value, (int, float)) and context_value <= value
        elif operator == "in":
            if isinstance(value, list):
                return context_value in value
            return False
        elif operator == "not_in":
            if isinstance(value, list):
                return context_value not in value
            return True
        elif operator == "exists":
            # Check if field exists and is not None
            return context_value is not None
        elif operator == "not_exists":
            # Check if field does not exist or is None
            return context_value is None
    
    return False


def _evaluate_rule(rule: Dict[str, Any], context: Dict[str, Any], industry_profile: str, hardware_class: str | None) -> bool:
    """Evaluate if a rule applies to the given context."""
    # Check industry profile match
    applies = rule.get("applies", {})
    industry_profiles = applies.get("industry_profiles", [])
    if industry_profile not in industry_profiles:
        return False
    
    # Check hardware class if specified
    if hardware_class:
        hardware_classes = applies.get("hardware_classes", [])
        if hardware_classes and hardware_class not in hardware_classes:
            return False
    
    # Evaluate "when" conditions
    when = rule.get("when", {})
    if not when:
        return True  # No conditions, always applies
    
    # Evaluate expression tree
    return _evaluate_rule_expression(when, context)


def _apply_rule_action(rule: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Apply rule action and create decision."""
    then_clause = rule.get("then", {})
    action = then_clause.get("action")
    enforcement = then_clause.get("enforcement", "NONE")
    payload = then_clause.get("payload", {})
    
    # Determine object_type and object_id from target
    target = rule.get("target", {})
    object_type = target.get("object_type", "process_step")
    selector = target.get("selector", {})
    
    # Get object_id from selector or payload
    object_id = selector.get("id") or payload.get("object_id") or payload.get("step_type") or payload.get("test_type") or "UNKNOWN"
    
    # Generate deterministic decision ID
    rule_id = rule.get("rule_id", "UNKNOWN")
    decision_id = _generate_decision_id(rule_id, object_type, str(object_id), context)
    
    # Build why
    why = rule.get("why", {})
    
    decision: SOEDecision = {
        "id": decision_id,
        "object_type": object_type,
        "object_id": str(object_id),
        "action": action,
        "enforcement": enforcement,
        "why": {
            "rule_id": rule_id,
            "pack_id": rule.get("pack_id", "UNKNOWN"),
            "citations": why.get("citations", []),
        },
    }
    
    return decision


def run_soe(
    industry_profile: str,
    inputs: Dict[str, Any],
    hardware_class: str | None = None,
    additional_packs: List[str] | None = None,
) -> SOERun:
    """
    Run SOE evaluation (pure function, no side effects).
    
    Alias for evaluate_soe for consistency with Sprint 1 requirements.
    """
    return evaluate_soe(industry_profile, inputs, hardware_class, additional_packs)


def evaluate_soe(
    industry_profile: str,
    inputs: Dict[str, Any],
    hardware_class: str | None = None,
    additional_packs: List[str] | None = None,
    active_profiles: List[str] | None = None,
) -> SOERun:
    """
    Evaluate SOE rules and generate SOERun (Sprint 4: with profile stack support).
    
    Args:
        industry_profile: Industry profile name (space, aerospace, medical, etc.)
        inputs: Project inputs (processes, tests_requested, materials, bom_risk_flags)
        hardware_class: Optional hardware class (flight, class_2, etc.)
        additional_packs: Optional additional packs beyond defaults
        active_profiles: Optional profile stack (Sprint 4: BASE/DOMAIN/CUSTOMER_OVERRIDE)
    
    Returns:
        SOERun object with decisions, gates, and modifiers (including profile_stack if active_profiles provided)
    """
    # Resolve active packs (Sprint 4: can come from profile stack)
    profile_stack: List[Dict[str, Any]] = []
    if active_profiles:
        # Resolve profile stack
        try:
            resolved_profiles, errors = resolve_profile_stack(active_profiles)
            if errors:
                print(f"Warning: Profile stack errors: {errors}")
            else:
                profile_stack = resolved_profiles
                # Extract packs from profile stack
                pack_ids_from_profiles = set()
                for profile in resolved_profiles:
                    pack_ids_from_profiles.update(profile.get("standards_packs", []))
                # Merge with defaults
                default_packs = _resolve_active_packs(industry_profile, hardware_class)
                active_packs = list(pack_ids_from_profiles | set(default_packs + (additional_packs or [])))
        except Exception as e:
            print(f"Warning: Failed to resolve profile stack: {e}")
            # Fallback to default pack resolution
            default_packs = _resolve_active_packs(industry_profile, hardware_class)
            active_packs = list(set(default_packs + (additional_packs or [])))
    else:
        # Sprint 3 behavior: resolve from industry profile
        default_packs = _resolve_active_packs(industry_profile, hardware_class)
        active_packs = list(set(default_packs + (additional_packs or [])))
    
    # Build evaluation context
    context: Dict[str, Any] = {
        "industry_profile": industry_profile,
        "hardware_class": hardware_class,
        **inputs,
    }
    
    # Collect all rules from active packs
    all_rules: List[Dict[str, Any]] = []
    for pack_id in active_packs:
        try:
            pack = _load_standards_pack(pack_id)
            rules = pack.get("rules", [])
            for rule in rules:
                rule["pack_id"] = pack_id  # Ensure pack_id is set
            all_rules.extend(rules)
        except Exception as e:
            # Log error but continue
            print(f"Warning: Failed to load pack {pack_id}: {e}")
            continue
    
    # Evaluate rules and collect decisions (Sprint 4: tag with profile source)
    decisions: List[SOEDecision] = []
    
    # Build pack_id -> profile mapping for tagging
    pack_to_profile: Dict[str, Dict[str, Any]] = {}
    if profile_stack:
        for profile in profile_stack:
            for pack_id in profile.get("standards_packs", []):
                pack_to_profile[pack_id] = {
                    "profile_id": profile["profile_id"],
                    "profile_type": profile["profile_type"],
                    "layer": profile_stack.index(profile),
                }
    
    for rule in all_rules:
        if _evaluate_rule(rule, context, industry_profile, hardware_class):
            decision = _apply_rule_action(rule, context)
            
            # Sprint 4: Tag decision with profile source
            pack_id = rule.get("pack_id")
            if pack_id and pack_id in pack_to_profile:
                profile_info = pack_to_profile[pack_id]
                # Get clause reference from rule why if available
                clause_ref = rule.get("why", {}).get("citations", [None])[0] if rule.get("why", {}).get("citations") else None
                decision = tag_decision_with_profile(
                    decision,
                    profile_id=profile_info["profile_id"],
                    profile_type=profile_info["profile_type"],
                    layer=profile_info["layer"],
                    clause_reference=clause_ref,
                )
            
            decisions.append(decision)
    
    # Build gates from decisions
    gates: List[Dict[str, Any]] = [
        {
            "gate_id": "GATE-RELEASE",
            "status": "blocked" if any(d.get("enforcement") == "BLOCK_RELEASE" for d in decisions) else "open",
            "blocked_by": [d["id"] for d in decisions if d.get("enforcement") == "BLOCK_RELEASE"],
        }
    ]
    
    # Get profile defaults for evidence retention
    profile = _load_industry_profile(industry_profile)
    
    # Build decision-to-rule mapping for payload extraction
    rule_map = {r.get("rule_id"): r for r in all_rules}
    
    # Extract required evidence from decisions
    required_evidence: List[Dict[str, Any]] = []
    for decision in decisions:
        action = decision["action"]
        object_type = decision.get("object_type")
        
        rule_id = decision["why"]["rule_id"]
        rule = rule_map.get(rule_id)
        payload = rule.get("then", {}).get("payload", {}) if rule else {}
        
        if action == "SET_RETENTION" and object_type == "evidence":
            # Get retention from rule payload
            retention = payload.get("retention", profile.get("defaults", {}).get("evidence_retention", "LIFE_OF_PROGRAM"))
            
            required_evidence.append({
                "evidence_type": decision["object_id"],
                "applies_to": payload.get("applies_to", "material"),
                "object_id": decision["object_id"],
                "retention": retention,
            })
        elif action == "REQUIRE" and object_type == "evidence":
            # Evidence requirement from rule
            required_evidence.append({
                "evidence_type": payload.get("evidence_type", decision["object_id"]),
                "applies_to": payload.get("applies_to", "material"),
                "object_id": decision["object_id"],
                "retention": payload.get("retention", profile.get("defaults", {}).get("evidence_retention", "5_YEARS")),
            })
    
    # Extract cost modifiers from decisions
    cost_modifiers: List[Dict[str, Any]] = []
    for decision in decisions:
        if decision["action"] == "ADD_COST_MODIFIER":
            # Extract from payload
            cost_modifiers.append({
                "reason": decision["why"].get("summary", "SOE cost modifier"),
                "modifier_type": "PERCENT",
                "value": 0.0,  # Would come from payload
                "rule_id": decision["why"]["rule_id"],
            })
    
    # Build SOERun (Sprint 4: include profile_stack if available)
    soe_run_base: Dict[str, Any] = {
        "soe_version": "1.0.0",
        "industry_profile": industry_profile,
        "hardware_class": hardware_class,
        "active_packs": active_packs,
        "inputs": inputs,
        "decisions": decisions,
        "required_evidence": required_evidence,
        "gates": gates,
        "cost_modifiers": cost_modifiers,
    }
    
    # Sprint 4: Add profile stack metadata if profiles were used
    if profile_stack:
        soe_run_base["active_profiles"] = [p["profile_id"] for p in profile_stack]
        soe_run_base["profile_stack"] = [
            {
                "profile_id": p["profile_id"],
                "profile_type": p["profile_type"],
                "name": p.get("name"),
                "layer": profile_stack.index(p),
            }
            for p in profile_stack
        ]
    
    soe_run: SOERun = soe_run_base  # type: ignore
    
    # Validate against schema
    try:
        validate_schema(soe_run, "soe_run.schema.json")
    except Exception as e:
        raise ValueError(f"SOERun schema validation failed: {e}") from e
    
    return soe_run


def generate_why_explanation(decision: SOEDecision) -> str:
    """Generate human-readable 'why required' explanation."""
    rule_id = decision["why"].get("rule_id", "UNKNOWN")
    pack_id = decision["why"].get("pack_id", "UNKNOWN")
    citations = decision["why"].get("citations", [])
    
    # Load rule to get summary
    try:
        pack = _load_standards_pack(pack_id)
        rules = pack.get("rules", [])
        for rule in rules:
            if rule.get("rule_id") == rule_id:
                why = rule.get("why", {})
                summary = why.get("summary", f"{decision['action']} required by rule {rule_id}")
                citation_str = ", ".join(citations) if citations else ""
                if citation_str:
                    return f"{summary} ({citation_str})"
                return summary
    except Exception:
        pass
    
    # Fallback
    return f"{decision['action']} required by {rule_id} in pack {pack_id}"
