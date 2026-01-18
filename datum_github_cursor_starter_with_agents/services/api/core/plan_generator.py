"""Datum Plan generator - generates deterministic plans from rules and quotes."""

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


class PlanStep(TypedDict):
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


def _generate_id(prefix: str = "plan") -> str:
    """Generate a unique ID."""
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


def _create_default_steps(quote: Dict[str, Any]) -> List[PlanStep]:
    """Create default process steps for a quote."""
    steps: List[PlanStep] = []
    sequence = 1
    
    # PCB Fabrication
    steps.append({
        "step_id": _generate_id("step"),
        "type": "FAB",
        "title": "PCB Fabrication",
        "sequence": sequence,
        "required": True,
        "locked_sequence": False,
        "parameters": None,
        "acceptance": {
            "criteria": "IPC-A-600 Class 3",
            "sampling": "100_PERCENT",
        },
        "source_rules": [],
    })
    sequence += 1
    
    # Assembly
    assembly_sides = quote.get("assumptions", {}).get("assembly_sides", ["TOP"])
    if "TOP" in assembly_sides:
        steps.append({
            "step_id": _generate_id("step"),
            "type": "ASSEMBLY",
            "title": "Top-side Assembly",
            "sequence": sequence,
            "required": True,
            "locked_sequence": False,
            "parameters": {"side": "TOP"},
            "acceptance": {
                "criteria": "IPC-A-610 Class 3",
                "sampling": "100_PERCENT",
            },
            "source_rules": [],
        })
        sequence += 1
    
    if "BOTTOM" in assembly_sides:
        steps.append({
            "step_id": _generate_id("step"),
            "type": "ASSEMBLY",
            "title": "Bottom-side Assembly",
            "sequence": sequence,
            "required": True,
            "locked_sequence": False,
            "parameters": {"side": "BOTTOM"},
            "acceptance": {
                "criteria": "IPC-A-610 Class 3",
                "sampling": "100_PERCENT",
            },
            "source_rules": [],
        })
        sequence += 1
    
    # Final Inspection
    steps.append({
        "step_id": _generate_id("step"),
        "type": "INSPECT",
        "title": "Final Inspection",
        "sequence": sequence,
        "required": True,
        "locked_sequence": False,
        "parameters": None,
        "acceptance": {
            "criteria": "Visual inspection per IPC-A-610",
            "sampling": "100_PERCENT",
        },
        "source_rules": [],
    })
    sequence += 1
    
    # Pack
    steps.append({
        "step_id": _generate_id("step"),
        "type": "PACK",
        "title": "Packaging",
        "sequence": sequence,
        "required": True,
        "locked_sequence": False,
        "parameters": None,
        "acceptance": None,
        "source_rules": [],
    })
    
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
                new_step: PlanStep = {
                    "step_id": _generate_id("step"),
                    "type": step_type,
                    "title": step_title,
                    "sequence": sequence_counter,
                    "required": payload.get("required", True),
                    "locked_sequence": payload.get("lock_sequence", False),
                    "parameters": payload.get("parameters"),
                    "acceptance": payload.get("acceptance"),
                    "source_rules": [source_rule],
                }
                new_steps.append(new_step)
                
                if payload.get("lock_sequence", False):
                    locked_sequences.add(sequence_counter)
            
            elif action_type == "LOCK_SEQUENCE":
                # Lock a sequence of steps and add them if they don't exist
                steps_to_lock = payload.get("steps", [])
                lock_sequence = payload.get("lock_sequence", True)
                
                # Step type mapping for NASA polymerics
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
                        new_step: PlanStep = {
                            "step_id": _generate_id("step"),
                            "type": step_type,
                            "title": step_name.replace("_", " ").title(),
                            "sequence": sequence_counter,
                            "required": True,
                            "locked_sequence": lock_sequence,
                            "parameters": None,
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
                new_step: PlanStep = {
                    "step_id": _generate_id("step"),
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
    Convert SOE decisions to plan steps (non-destructively).
    
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
        
        if existing_step:
            # Mark existing step as SOE-required
            existing_step["required"] = True
            if decision.get("enforcement") == "BLOCK_RELEASE":
                existing_step["locked_sequence"] = True
            # Add SOE source rule
            soe_rule_ref = {
                "rule_id": decision["why"]["rule_id"],
                "ruleset_version": 1,  # SOE ruleset version
                "justification": f"SOE: {decision['why'].get('citations', [decision['why']['rule_id']])}",
            }
            if soe_rule_ref not in existing_step.get("source_rules", []):
                existing_step["source_rules"].append(soe_rule_ref)
        else:
            # Create new SOE-required step
            sequence_counter += 1
            
            # Determine step type and title
            step_type_map = {
                "CLEAN": "CLEAN",
                "BAKE": "BAKE",
                "POLYMER": "POLYMER",
                "CURE": "CURE",
                "INSPECT": "INSPECT",
                "TVAC": "TEST",
                "XRAY": "TEST",
            }
            
            step_type = step_type_map.get(object_id, "ASSEMBLY" if object_type == "process_step" else "TEST")
            step_title = object_id.replace("_", " ").title()
            
            new_step: PlanStep = {
                "step_id": _generate_id("step"),
                "type": step_type,
                "title": step_title,
                "sequence": sequence_counter,
                "required": True,
                "locked_sequence": decision.get("enforcement") == "BLOCK_RELEASE",
                "parameters": {"test_type": object_id} if step_type == "TEST" else None,
                "acceptance": {
                    "criteria": f"SOE requirement: {decision['why'].get('citations', [decision['why']['rule_id']])}",
                    "sampling": "100_PERCENT",
                } if step_type in ("TEST", "INSPECT") else None,
                "source_rules": [{
                    "rule_id": decision["why"]["rule_id"],
                    "ruleset_version": 1,  # SOE ruleset
                    "justification": f"SOE: {decision['why'].get('citations', [decision['why']['rule_id']])}",
                }],
            }
            new_steps.append(new_step)
    
    return new_steps


def generate_plan(
    quote_id: str,
    ruleset_version: int = 1,
    org_id: str | None = None,
    design_id: str | None = None,
) -> Dict[str, Any]:
    """
    Generate a DatumPlan from a quote and ruleset.
    
    Args:
        quote_id: ID of the quote to generate plan from
        ruleset_version: Version of ruleset to use
        org_id: Organization ID (defaults to quote's org_id)
        design_id: Design ID (defaults to quote's design_id)
    
    Returns:
        DatumPlan object
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
    steps = _create_default_steps(quote)
    
    # Convert rule actions to steps
    rule_steps = _convert_rule_actions_to_steps(traces, steps)
    steps.extend(rule_steps)
    
    # Inject SOE-enforced steps if SOERun exists
    soe_run = get_soe_run(quote_id=quote_id)
    if soe_run:
        soe_steps = _convert_soe_decisions_to_steps(soe_run, steps)
        steps.extend(soe_steps)
    
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
    
    # Build plan payload
    plan: Dict[str, Any] = {
        "id": plan_id,
        "org_id": org_id,
        "design_id": design_id,
        "revision_id": revision_id,
        "quote_id": quote_id,
        "quote_version": quote.get("quote_version", 1),
        "plan_revision": plan_revision,
        "locked": False,
        "derived_from_ruleset": {
            "ruleset_id": "ruleset_default",
            "ruleset_version": ruleset_version,
        },
        "steps": steps,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    
    # Validate against schema
    try:
        validate_schema(plan, "datum_plan.schema.json")
    except Exception as e:
        raise ValueError(f"Plan schema validation failed: {e}") from e
    
    # Save plan
    save_plan(plan)
    
    return plan
