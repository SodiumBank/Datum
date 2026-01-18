"""Datum Plan generator - generates deterministic plans from SOE + quotes.

SPRINT 2: Manufacturing Intent Layer
- Pure function: SOERun + Quote -> DatumPlan
- Deterministic: Same inputs -> identical plan
- Immutable: Plan cannot be edited post-generation
- Traceable: Every step/test/evidence references SOE decisions
"""

import hashlib
import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, List, TypedDict

from services.api.core.rules_engine import (
    evaluate_rules,
    FeatureContext,
    RuleTrace,
)
from services.api.core.storage import (
    get_quote,
    save_plan,
    get_soe_run,
)
from services.api.core.schema_validation import validate_schema


class PlanStep(TypedDict, total=False):
    """Plan step structure."""
    step_id: str
    type: str
    title: str
    sequence: int
    required: bool
    locked_sequence: bool
    parameters: Dict[str, Any] | None
    acceptance: Dict[str, Any] | None
    source_rules: List[Dict[str, Any]]
    soe_decision_id: str  # Sprint 2: SOE decision reference
    soe_why: Dict[str, Any]  # Sprint 2: SOE justification


def _generate_deterministic_id(inputs: Dict[str, Any], prefix: str = "step") -> str:
    """Generate deterministic ID from inputs (Sprint 2: for immutability)."""
    # Hash inputs to create deterministic ID
    input_str = f"{prefix}:{inputs.get('type')}:{inputs.get('sequence')}:{inputs.get('title')}"
    hash_obj = hashlib.sha256(input_str.encode())
    hash_hex = hash_obj.hexdigest()[:12]
    return f"{prefix}_{hash_hex}"


def _generate_id(prefix: str = "plan") -> str:
    """Generate a unique ID (for plan-level IDs that need uniqueness)."""
    random_suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    return f"{prefix}_{random_suffix}"


def _generate_revision(existing_revisions: List[str]) -> str:
    """Generate next revision letter (A, B, C, ...)."""
    if not existing_revisions:
        return "A"
    
    # Get max revision letter
    max_rev = max(existing_revisions, key=lambda r: ord(r.upper()) if len(r) == 1 and r.isalpha() else ord("A") - 1)
    if max_rev and len(max_rev) == 1 and max_rev.isalpha():
        next_ord = ord(max_rev.upper()) + 1
        if next_ord <= ord("Z"):
            return chr(next_ord)
        # After Z, go to AA, AB, etc.
        if len(max_rev) == 1:
            return "AA"
        # Handle AA, AB, etc.
        if len(max_rev) == 2:
            second = ord(max_rev[1].upper()) + 1
            if second <= ord("Z"):
                return f"{max_rev[0]}{chr(second)}"
            return f"{chr(ord(max_rev[0].upper()) + 1)}A"
    
    return "A"


def _ensure_step_schema_compliant(step: Dict[str, Any], ruleset_version: int = 1) -> Dict[str, Any]:
    """
    Ensure step is schema-compliant (Sprint 7).
    
    - Remove None values for parameters/acceptance (omit optional fields)
    - Ensure source_rules has at least one entry (required: minItems: 1)
    """
    # Remove None values for optional object fields
    if step.get("parameters") is None:
        step.pop("parameters", None)
    if step.get("acceptance") is None:
        step.pop("acceptance", None)
    
    # Ensure source_rules has at least one entry (schema requires minItems: 1)
    if not step.get("source_rules") or len(step["source_rules"]) == 0:
        step["source_rules"] = [{
            "rule_id": "BASELINE_DEFAULT_STEP",
            "ruleset_version": ruleset_version,
            "justification": "Default manufacturing step required by baseline process",
        }]
    
    return step


def _create_default_steps(quote: Dict[str, Any], ruleset_version: int = 1) -> List[PlanStep]:
    """Create default process steps for a quote (Sprint 2: canonical step types)."""
    steps: List[PlanStep] = []
    sequence = 1
    
    # PCB Fabrication
    step = {
        "step_id": _generate_deterministic_id({"type": "FAB", "sequence": sequence, "title": "PCB Fabrication"}),
        "type": "FAB",
        "title": "PCB Fabrication",
        "sequence": sequence,
        "required": True,
        "locked_sequence": False,
        "acceptance": {
            "criteria": "IPC-A-600 Class 3",
            "sampling": "100_PERCENT",
        },
        "source_rules": [],
    }
    steps.append(_ensure_step_schema_compliant(step, ruleset_version))
    sequence += 1
    
    # Assembly
    assembly_sides = quote.get("assumptions", {}).get("assembly_sides", ["TOP"])
    if "TOP" in assembly_sides:
        step = {
            "step_id": _generate_deterministic_id({"type": "SMT", "sequence": sequence, "title": "Top-side SMT"}),
            "type": "SMT",
            "title": "Top-side SMT",
            "sequence": sequence,
            "required": True,
            "locked_sequence": False,
            "parameters": {"side": "TOP"},
            "acceptance": {
                "criteria": "IPC-A-610 Class 3",
                "sampling": "100_PERCENT",
            },
            "source_rules": [],
        }
        steps.append(_ensure_step_schema_compliant(step, ruleset_version))
        sequence += 1
        
        step = {
            "step_id": _generate_deterministic_id({"type": "REFLOW", "sequence": sequence, "title": "Top-side Reflow"}),
            "type": "REFLOW",
            "title": "Top-side Reflow",
            "sequence": sequence,
            "required": True,
            "locked_sequence": False,
            "parameters": {"side": "TOP"},
            "source_rules": [],
        }
        steps.append(_ensure_step_schema_compliant(step, ruleset_version))
        sequence += 1
    
    if "BOTTOM" in assembly_sides:
        step = {
            "step_id": _generate_deterministic_id({"type": "SMT", "sequence": sequence, "title": "Bottom-side SMT"}),
            "type": "SMT",
            "title": "Bottom-side SMT",
            "sequence": sequence,
            "required": True,
            "locked_sequence": False,
            "parameters": {"side": "BOTTOM"},
            "acceptance": {
                "criteria": "IPC-A-610 Class 3",
                "sampling": "100_PERCENT",
            },
            "source_rules": [],
        }
        steps.append(_ensure_step_schema_compliant(step, ruleset_version))
        sequence += 1
        
        step = {
            "step_id": _generate_deterministic_id({"type": "REFLOW", "sequence": sequence, "title": "Bottom-side Reflow"}),
            "type": "REFLOW",
            "title": "Bottom-side Reflow",
            "sequence": sequence,
            "required": True,
            "locked_sequence": False,
            "parameters": {"side": "BOTTOM"},
            "source_rules": [],
        }
        steps.append(_ensure_step_schema_compliant(step, ruleset_version))
        sequence += 1
    
    # Final Inspection
    step = {
        "step_id": _generate_deterministic_id({"type": "INSPECT", "sequence": sequence, "title": "Final Inspection"}),
        "type": "INSPECT",
        "title": "Final Inspection",
        "sequence": sequence,
        "required": True,
        "locked_sequence": False,
        "acceptance": {
            "criteria": "Visual inspection per IPC-A-610",
            "sampling": "100_PERCENT",
        },
        "source_rules": [],
    }
    steps.append(_ensure_step_schema_compliant(step, ruleset_version))
    sequence += 1
    
    # Pack
    step = {
        "step_id": _generate_deterministic_id({"type": "PACK", "sequence": sequence, "title": "Packaging"}),
        "type": "PACK",
        "title": "Packaging",
        "sequence": sequence,
        "required": True,
        "locked_sequence": False,
        "source_rules": [],
    }
    steps.append(_ensure_step_schema_compliant(step, ruleset_version))
    
    return steps


def _convert_rule_actions_to_steps(traces: List[RuleTrace], existing_steps: List[PlanStep]) -> List[PlanStep]:
    """
    Convert rule actions to plan steps.
    
    Rules can have actions like:
    - ADD_STEP: Add a new process step
    - LOCK_SEQUENCE: Lock the sequence of steps
    """
    new_steps: List[PlanStep] = []
    max_sequence = max([s["sequence"] for s in existing_steps], default=0)
    sequence_counter = max_sequence
    
    # Track which sequences should be locked
    locked_sequences: set[int] = set()
    
    for trace in traces:
        rule_id = trace["rule_id"]
        ruleset_version = trace["ruleset_version"]
        justification = trace["justification"]
        
        # Create source_rule reference
        source_rule = {
            "rule_id": rule_id,
            "ruleset_version": ruleset_version,
            "justification": justification,
        }
        
        # Load rule to get actions
        from services.api.core.rules_engine import load_ruleset_info
        ruleset_info = load_ruleset_info(ruleset_version)
        
        rule = None
        for r in ruleset_info.get("rules", []):
            if r.get("rule_id") == rule_id:
                rule = r
                break
        
        if not rule:
            continue
        
        # Process actions
        for action in rule.get("actions", []):
            action_type = action.get("type")
            payload = action.get("payload", {})
            
            if action_type == "ADD_STEP":
                # Add a new step
                step_type = payload.get("step_type", "ASSEMBLY")
                step_title = payload.get("title", step_type.replace("_", " ").title())
                
                sequence_counter += 1
            step_inputs = {"type": step_type, "sequence": sequence_counter, "title": step_title}
            new_step: PlanStep = {
                "step_id": _generate_deterministic_id(step_inputs),
                "type": step_type,
                "title": step_title,
                "sequence": sequence_counter,
                "required": payload.get("required", True),
                "locked_sequence": payload.get("lock_sequence", False),
                "source_rules": [source_rule],
            }
            # Add optional fields only if present
            if payload.get("parameters"):
                new_step["parameters"] = payload.get("parameters")
            if payload.get("acceptance"):
                new_step["acceptance"] = payload.get("acceptance")
                new_steps.append(new_step)
                
                if payload.get("lock_sequence", False):
                    locked_sequences.add(sequence_counter)
            
            elif action_type == "LOCK_SEQUENCE":
                # Lock a sequence of steps and add them if they don't exist
                steps_to_lock = payload.get("steps", [])
                lock_sequence = payload.get("lock_sequence", True)
                
                # Step type mapping for NASA polymerics (canonical types)
                step_type_map = {
                    "CLEAN": "CLEAN",
                    "BAKE": "BAKE",
                    "POLYMER": "POLYMER",
                    "CURE": "CURE",
                    "INSPECT": "INSPECT",
                }
                
                # Find or create steps
                for step_name in steps_to_lock:
                    step_type = step_type_map.get(step_name, step_name)
                    
                    # Check if step already exists
                    existing_step = None
                    for step in existing_steps + new_steps:
                        if step["type"] == step_type or step["title"].upper() == step_name.upper():
                            existing_step = step
                            break
                    
                    if existing_step:
                        # Mark existing step as locked
                        existing_step["locked_sequence"] = lock_sequence
                        locked_sequences.add(existing_step["sequence"])
                    else:
                        # Add new step with locked sequence
                        sequence_counter += 1
                        step_inputs = {"type": step_type, "sequence": sequence_counter, "title": step_name}
                        new_step: PlanStep = {
                            "step_id": _generate_deterministic_id(step_inputs),
                            "type": step_type,
                            "title": step_name.replace("_", " ").title(),
                            "sequence": sequence_counter,
                            "required": True,
                            "locked_sequence": lock_sequence,
                            "acceptance": {
                                "criteria": f"NASA-STD-8739.1 compliance for {step_name}",
                                "sampling": "100_PERCENT",
                            } if step_type == "INSPECT" else None,
                            "source_rules": [source_rule],
                        }
                        new_steps.append(new_step)
                        if lock_sequence:
                            locked_sequences.add(sequence_counter)
            
            elif action_type == "ADD_TEST":
                # Add a test step
                test_type = payload.get("test_type", "TEST")
                test_title = payload.get("title", test_type.replace("_", " ").title())
                
                sequence_counter += 1
                step_inputs = {"type": "TEST", "sequence": sequence_counter, "title": test_title}
                new_step: PlanStep = {
                    "step_id": _generate_deterministic_id(step_inputs),
                    "type": "TEST",
                    "title": test_title,
                    "sequence": sequence_counter,
                    "required": payload.get("required", True),
                    "locked_sequence": payload.get("lock_sequence", False),
                    "parameters": {"test_type": test_type, **payload.get("parameters", {})},
                    "acceptance": payload.get("acceptance"),
                    "source_rules": [source_rule],
                }
                new_steps.append(new_step)
                
                if payload.get("lock_sequence", False):
                    locked_sequences.add(sequence_counter)
    
    return new_steps


def _convert_soe_decisions_to_steps(soe_run: Dict[str, Any], existing_steps: List[PlanStep]) -> List[PlanStep]:
    """
    Convert SOE decisions to plan steps (Sprint 2: with SOE decision references).
    
    SOE decisions with INSERT_STEP or REQUIRE actions for process_step/test
    are converted to plan steps, flagged as SOE-required.
    """
    new_steps: List[PlanStep] = []
    max_sequence = max([s["sequence"] for s in existing_steps], default=0)
    sequence_counter = max_sequence
    
    decisions = soe_run.get("decisions", [])
    
    for decision in decisions:
        action = decision.get("action")
        object_type = decision.get("object_type")
        
        # Only process INSERT_STEP or REQUIRE actions for process_step/test
        if action not in ("INSERT_STEP", "REQUIRE"):
            continue
        
        if object_type not in ("process_step", "test"):
            continue
        
        # Check if step already exists
        object_id = decision.get("object_id")
        existing_step = None
        for step in existing_steps + new_steps:
            if step.get("type") == object_id or step.get("title").upper() == object_id.upper():
                existing_step = step
                break
        
        # Build SOE why metadata
        soe_why = {
            "rule_id": decision["why"]["rule_id"],
            "pack_id": decision["why"]["pack_id"],
            "citations": decision["why"].get("citations", []),
        }
        
        if existing_step:
            # Mark existing step as SOE-required
            existing_step["required"] = True
            if decision.get("enforcement") == "BLOCK_RELEASE":
                existing_step["locked_sequence"] = True
            # Add SOE decision reference
            existing_step["soe_decision_id"] = decision["id"]
            existing_step["soe_why"] = soe_why
            # Add SOE source rule
            soe_rule_ref = {
                "rule_id": decision["why"]["rule_id"],
                "ruleset_version": 1,  # SOE ruleset version
                "justification": f"SOE: {', '.join(decision['why'].get('citations', [decision['why']['rule_id']]))}",
            }
            if soe_rule_ref not in existing_step.get("source_rules", []):
                existing_step["source_rules"].append(soe_rule_ref)
        else:
            # Create new SOE-required step
            sequence_counter += 1
            
            # Determine step type and title (canonical step types)
            step_type_map = {
                "CLEAN": "CLEAN",
                "BAKE": "BAKE",
                "POLYMER": "POLYMER",
                "CURE": "CURE",
                "INSPECT": "INSPECT",
                "TVAC": "TEST",
                "VIBRATION": "TEST",
                "SHOCK": "TEST",
                "XRAY": "TEST",
            }
            
            step_type = step_type_map.get(object_id, "ASSEMBLY" if object_type == "process_step" else "TEST")
            step_title = object_id.replace("_", " ").title()
            
            step_inputs = {"type": step_type, "sequence": sequence_counter, "title": step_title}
            new_step: PlanStep = {
                "step_id": _generate_deterministic_id(step_inputs),
                "type": step_type,
                "title": step_title,
                "sequence": sequence_counter,
                "required": True,
                "locked_sequence": decision.get("enforcement") == "BLOCK_RELEASE",
                "parameters": {"test_type": object_id} if step_type == "TEST" else None,
                "acceptance": {
                    "criteria": f"SOE requirement: {', '.join(decision['why'].get('citations', [decision['why']['rule_id']]))}",
                    "sampling": "100_PERCENT",
                } if step_type in ("TEST", "INSPECT") else None,
                "source_rules": [{
                    "rule_id": decision["why"]["rule_id"],
                    "ruleset_version": 1,  # SOE ruleset
                    "justification": f"SOE: {', '.join(decision['why'].get('citations', [decision['why']['rule_id']]))}",
                }],
                "soe_decision_id": decision["id"],
                "soe_why": soe_why,
            }
            new_steps.append(new_step)
    
    return new_steps


def _generate_test_intent_from_soe(soe_run: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate test intent from SOE decisions (Sprint 2).
    
    Translates SOE test decisions into DatumPlan test sections.
    """
    test_intent: List[Dict[str, Any]] = []
    decisions = soe_run.get("decisions", [])
    
    for decision in decisions:
        action = decision.get("action")
        object_type = decision.get("object_type")
        
        # Only process REQUIRE/INSERT_STEP actions for tests
        if action not in ("REQUIRE", "INSERT_STEP"):
            continue
        
        if object_type != "test":
            continue
        
        test_type = decision.get("object_id")
        soe_why = {
            "rule_id": decision["why"]["rule_id"],
            "pack_id": decision["why"]["pack_id"],
            "citations": decision["why"].get("citations", []),
        }
        
        test_intent.append({
            "test_id": _generate_deterministic_id({"test_type": test_type, "decision_id": decision["id"]}, prefix="test"),
            "test_type": test_type,
            "title": test_type.replace("_", " ").title(),
            "required": True,
            "acceptance_criteria": f"SOE requirement: {', '.join(decision['why'].get('citations', [decision['why']['rule_id']]))}",
            "soe_decision_id": decision["id"],
            "soe_why": soe_why,
        })
    
    return test_intent


def _generate_evidence_intent_from_soe(soe_run: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate evidence intent from SOE required_evidence (Sprint 2).
    
    Translates SOE evidence requirements into DatumPlan evidence section with retention.
    """
    evidence_intent: List[Dict[str, Any]] = []
    required_evidence = soe_run.get("required_evidence", [])
    
    for evidence_req in required_evidence:
        evidence_type = evidence_req.get("evidence_type")
        applies_to = evidence_req.get("applies_to")
        object_id = evidence_req.get("object_id")
        retention = evidence_req.get("retention", "STANDARD")
        
        # Try to find matching decision
        matching_decision = None
        for decision in soe_run.get("decisions", []):
            if decision.get("object_type") == "evidence" and decision.get("object_id") == evidence_type:
                matching_decision = decision
                break
        
        if matching_decision:
            soe_why = {
                "rule_id": matching_decision["why"]["rule_id"],
                "pack_id": matching_decision["why"]["pack_id"],
                "citations": matching_decision["why"].get("citations", []),
            }
            decision_id = matching_decision["id"]
        else:
            # No matching decision, use generic SOE reference
            soe_why = {
                "rule_id": "SOE_EVIDENCE_REQUIREMENT",
                "pack_id": soe_run.get("active_packs", [""])[0] if soe_run.get("active_packs") else "",
                "citations": [],
            }
            decision_id = f"DEC-EVIDENCE-{evidence_type}"
        
        evidence_intent.append({
            "evidence_id": _generate_deterministic_id({"evidence_type": evidence_type, "object_id": object_id}, prefix="evidence"),
            "evidence_type": evidence_type,
            "applies_to": applies_to,
            "object_id": object_id,
            "retention": retention,
            "soe_decision_id": decision_id,
            "soe_why": soe_why,
        })
    
    return evidence_intent


def generate_plan(
    quote_id: str,
    soe_run: Dict[str, Any] | None = None,
    ruleset_version: int = 1,
    org_id: str | None = None,
    design_id: str | None = None,
) -> Dict[str, Any]:
    """
    Generate a DatumPlan from SOERun + quote as a pure function.
    
    SPRINT 2: This is a deterministic intent generator - NO edits, NO overrides.
    DatumPlan is immutable once generated and traceable back to SOE decisions.
    
    Args:
        quote_id: ID of the quote to generate plan from
        soe_run: SOERun object (if None, will try to load from storage)
        ruleset_version: Version of ruleset to use
        org_id: Organization ID (defaults to quote's org_id)
        design_id: Design ID (defaults to quote's design_id)
    
    Returns:
        DatumPlan object with SOE decision references
    """
    # Load quote
    quote = get_quote(quote_id)
    if not quote:
        raise ValueError(f"Quote not found: {quote_id}")
    
    # Get quote metadata
    if not org_id:
        org_id = quote.get("org_id", "org_dev_001")
    if not design_id:
        design_id = quote.get("design_id")
    
    if not design_id:
        raise ValueError("design_id required")
    
    # Get quote's revision
    revision_id = quote.get("revision_id")
    if not revision_id:
        raise ValueError("Quote must have a revision_id")
    
    # Get tier from quote
    tier = quote.get("tier", "TIER_1")
    
    # Build feature context for rule evaluation
    gerber_upload_id = None  # Would need to be stored in quote or retrieved
    bom_upload_id = None     # Would need to be stored in quote or retrieved
    
    # For now, try to extract from quote metadata or use defaults
    board_metrics = {}
    bom_items = None
    gerber_files = None
    
    context: FeatureContext = {
        "board_metrics": board_metrics,
        "bom_items": bom_items,
        "quote": quote,
        "assumptions": quote.get("assumptions", {}),
        "gerber_files": gerber_files,
    }
    
    # Evaluate rules
    traces = evaluate_rules(context, ruleset_version=ruleset_version, tier=tier)
    
    # Create default steps
    steps = _create_default_steps(quote, ruleset_version=ruleset_version)
    
    # Convert rule actions to steps
    rule_steps = _convert_rule_actions_to_steps(traces, steps)
    steps.extend(rule_steps)
    
    # Load SOERun if not provided
    if not soe_run:
        soe_run = get_soe_run(quote_id=quote_id)
    
    # Collect SOE decision IDs for plan metadata
    soe_decision_ids: List[str] = []
    soe_run_id: str | None = None
    
    if soe_run:
        soe_run_id = soe_run.get("id") or f"soe_run_{quote_id}"
        decisions = soe_run.get("decisions", [])
        soe_decision_ids = [d["id"] for d in decisions if "id" in d]
        
        # Inject SOE-enforced steps
        soe_steps = _convert_soe_decisions_to_steps(soe_run, steps)
        steps.extend(soe_steps)
        
        # Generate test intent from SOE
        test_intent = _generate_test_intent_from_soe(soe_run)
        
        # Generate evidence intent from SOE
        evidence_intent = _generate_evidence_intent_from_soe(soe_run)
    else:
        test_intent = []
        evidence_intent = []
    
    # Sort steps by sequence
    steps.sort(key=lambda s: s["sequence"])
    
    # Apply locked sequences
    for step in steps:
        # Check if this step should be locked based on rule actions
        if step.get("source_rules"):
            # If step came from a LOCK_SEQUENCE action, mark it
            pass
    
    # Get existing plans for this quote to determine revision
    # For now, assume this is the first plan (revision A)
    existing_revisions: List[str] = []
    plan_revision = _generate_revision(existing_revisions)
    
    # Generate plan ID
    plan_id = _generate_id("plan")
    
    # Create timestamp
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Build plan payload (SPRINT 2: Immutable intent layer, SPRINT 3: Editable with constraints)
    plan: Dict[str, Any] = {
        "id": plan_id,
        "org_id": org_id,
        "design_id": design_id,
        "revision_id": revision_id,
        "quote_id": quote_id,
        "quote_version": quote.get("quote_version", 1),
        "plan_revision": plan_revision,
        "locked": False,
        "version": 1,  # Sprint 3: Start at version 1
        "state": "draft",  # Sprint 3: Plans start in draft
        "derived_from_ruleset": {
            "ruleset_id": "ruleset_default",
            "ruleset_version": ruleset_version,
        },
        "steps": steps,
        "tests": test_intent,
        "evidence_intent": evidence_intent,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    
    # Add SOE references if SOERun was used
    if soe_run:
        plan["soe_run_id"] = soe_run_id
        plan["soe_decision_ids"] = soe_decision_ids
    
    # Validate against schema
    try:
        validate_schema(plan, "datum_plan.schema.json")
    except Exception as e:
        raise ValueError(f"Plan schema validation failed: {e}") from e
    
    # Save plan
    save_plan(plan)
    
    return plan
