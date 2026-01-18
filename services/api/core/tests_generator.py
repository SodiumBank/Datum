"""Datum Tests generator - generates declared tests from rules and plans."""

import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, List, TypedDict

from services.api.core.storage import (
    get_plan,
    get_quote,
    save_tests,
)
from services.api.core.rules_engine import (
    evaluate_rules,
    FeatureContext,
    load_ruleset_info,
)
from services.api.core.schema_validation import validate_schema


class DeclaredTest(TypedDict):
    """Declared test structure."""
    test_code: str
    category: str
    required: bool
    parameters: Dict[str, Any]
    acceptance: Dict[str, Any]
    source_rules: List[Dict[str, Any]]


def _generate_id(prefix: str = "test") -> str:
    """Generate a unique ID."""
    random_suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
    return f"{prefix}_{random_suffix}"


def _map_test_type_to_code(test_type: str) -> str:
    """Map rule test_type to DatumTests test_code enum."""
    mapping = {
        "XRAY": "XRAY",
        "AOI": "AOI",
        "ICT": "ICT",
        "FCT": "FCT",
        "PROGRAM_VERIFY": "PROGRAM_VERIFY",
        "TVAC": "TVAC",
        "THERMAL_CYCLE": "THERMAL_CYCLE",
        "VIBRATION_SINE": "VIBRATION_SINE",
        "VIBRATION_RANDOM": "VIBRATION_RANDOM",
        "SHOCK": "SHOCK",
        "DROP": "DROP",
        "BURN_IN": "BURN_IN",
        "HALT": "HALT",
        "HASS": "HASS",
    }
    return mapping.get(test_type.upper(), "AOI")  # Default to AOI


def _map_test_code_to_category(test_code: str) -> str:
    """Map test_code to category."""
    electrical = {"ICT", "FCT", "PROGRAM_VERIFY"}
    inspection = {"AOI", "XRAY"}
    environmental = {"THERMAL_CYCLE", "TVAC", "VIBRATION_SINE", "VIBRATION_RANDOM", "SHOCK", "DROP", "BURN_IN"}
    reliability = {"HALT", "HASS"}
    
    if test_code in electrical:
        return "ELECTRICAL"
    elif test_code in inspection:
        return "INSPECTION"
    elif test_code in environmental:
        return "ENVIRONMENTAL"
    elif test_code in reliability:
        return "RELIABILITY"
    else:
        return "MECHANICAL"


def _generate_default_tests(plan: Dict[str, Any]) -> List[DeclaredTest]:
    """Generate default tests based on plan assumptions."""
    tests: List[DeclaredTest] = []
    
    quote_id = plan.get("quote_id")
    quote = get_quote(quote_id) if quote_id else None
    assumptions = quote.get("assumptions", {}) if quote else {}
    
    # Add AOI for high-reliability assemblies
    ipc_class = assumptions.get("ipc_class", "CLASS_2")
    if ipc_class in ("CLASS_3", "CLASS_3A"):
        tests.append({
            "test_code": "AOI",
            "category": "INSPECTION",
            "required": True,
            "parameters": {
                "ipc_class": ipc_class,
                "reason": "High-reliability assembly requires AOI",
            },
            "acceptance": {
                "criteria": "IPC-A-610 Class 3 acceptance criteria",
                "retest_policy": "ONCE",
            },
            "source_rules": [],
        })
    
    # Add PROGRAM_VERIFY if programming is required
    # (This would be determined by BOM analysis - for now, skip if not explicit)
    
    return tests


def _convert_rule_tests_to_declared_tests(
    plan: Dict[str, Any],
    ruleset_version: int,
) -> List[DeclaredTest]:
    """
    Convert rule ADD_TEST actions to declared tests.
    
    Looks at plan steps that have TEST type and extracts from source_rules.
    """
    declared_tests: List[DeclaredTest] = []
    
    # Get test steps from plan
    steps = plan.get("steps", [])
    test_steps = [s for s in steps if s.get("type") == "TEST"]
    
    for step in test_steps:
        source_rules = step.get("source_rules", [])
        
        # Extract test information from step parameters
        parameters = step.get("parameters", {})
        test_type = parameters.get("test_type", "AOI")
        test_code = _map_test_type_to_code(test_type)
        category = _map_test_code_to_category(test_code)
        
        # Get acceptance criteria from step
        acceptance = step.get("acceptance", {})
        if not acceptance:
            # Default acceptance
            acceptance = {
                "criteria": f"Standard acceptance criteria for {test_code}",
                "retest_policy": "ONCE",
            }
        
        # Merge parameters
        test_parameters = {
            "test_type": test_type,
            **{k: v for k, v in parameters.items() if k != "test_type"},
        }
        
        declared_test: DeclaredTest = {
            "test_code": test_code,
            "category": category,
            "required": step.get("required", True),
            "parameters": test_parameters,
            "acceptance": acceptance,
            "source_rules": source_rules,
        }
        
        declared_tests.append(declared_test)
    
    # Also evaluate rules directly to find test requirements
    # (in case tests are declared without plan steps)
    quote_id = plan.get("quote_id")
    quote = get_quote(quote_id) if quote_id else None
    
    if quote:
        # Build feature context for rule evaluation
        assumptions = quote.get("assumptions", {})
        context: FeatureContext = {
            "board_metrics": {},
            "bom_items": None,
            "quote": quote,
            "assumptions": assumptions,
            "gerber_files": None,
        }
        
        # Evaluate rules
        traces = evaluate_rules(context, ruleset_version=ruleset_version, tier=quote.get("tier", "TIER_1"))
        
        # Load ruleset to get actions
        ruleset_info = load_ruleset_info(ruleset_version)
        
        # Process rule actions for tests
        for trace in traces:
            rule_id = trace["rule_id"]
            
            # Find rule
            rule = None
            for r in ruleset_info.get("rules", []):
                if r.get("rule_id") == rule_id:
                    rule = r
                    break
            
            if not rule:
                continue
            
            # Check if this test is already in declared_tests
            existing_test_codes = {t["test_code"] for t in declared_tests}
            
            # Process actions
            for action in rule.get("actions", []):
                if action.get("type") == "ADD_TEST":
                    payload = action.get("payload", {})
                    test_type = payload.get("test_type", "AOI")
                    test_code = _map_test_type_to_code(test_type)
                    
                    # Skip if already declared
                    if test_code in existing_test_codes:
                        continue
                    
                    category = _map_test_code_to_category(test_code)
                    
                    # Create source_rule reference
                    source_rule = {
                        "rule_id": rule_id,
                        "ruleset_version": trace["ruleset_version"],
                        "justification": trace["justification"],
                    }
                    
                    declared_test: DeclaredTest = {
                        "test_code": test_code,
                        "category": category,
                        "required": payload.get("required", True),
                        "parameters": payload.get("parameters", {"test_type": test_type}),
                        "acceptance": payload.get("acceptance", {
                            "criteria": trace["justification"],
                            "retest_policy": "ONCE",
                        }),
                        "source_rules": [source_rule],
                    }
                    
                    declared_tests.append(declared_test)
                    existing_test_codes.add(test_code)
    
    return declared_tests


def generate_tests(
    plan_id: str,
    ruleset_version: int | None = None,
) -> Dict[str, Any]:
    """
    Generate DatumTests from a plan and ruleset.
    
    Args:
        plan_id: ID of the plan to generate tests from
        ruleset_version: Version of ruleset to use (defaults to plan's ruleset version)
    
    Returns:
        DatumTests object
    """
    # Load plan
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")
    
    # Get ruleset version from plan if not provided
    if not ruleset_version:
        derived_from = plan.get("derived_from_ruleset", {})
        ruleset_version = derived_from.get("ruleset_version", 1)
    
    # Get plan metadata
    revision_id = plan.get("revision_id")
    if not revision_id:
        raise ValueError("Plan must have a revision_id")
    
    plan_revision = plan.get("plan_revision", "A")
    
    # Generate default tests
    default_tests = _generate_default_tests(plan)
    
    # Convert rule tests to declared tests
    rule_tests = _convert_rule_tests_to_declared_tests(plan, ruleset_version)
    
    # Merge tests (avoid duplicates by test_code)
    all_tests: List[DeclaredTest] = []
    seen_codes = set()
    
    for test in default_tests + rule_tests:
        test_code = test["test_code"]
        if test_code not in seen_codes:
            all_tests.append(test)
            seen_codes.add(test_code)
    
    # Generate tests ID
    tests_id = _generate_id("tests")
    
    # Create timestamp
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Build tests payload
    tests: Dict[str, Any] = {
        "id": tests_id,
        "revision_id": revision_id,
        "plan_id": plan_id,
        "plan_revision": plan_revision,
        "declared_tests": all_tests,
    }
    
    # Validate against schema
    try:
        validate_schema(tests, "datum_tests.schema.json")
    except Exception as e:
        raise ValueError(f"Tests schema validation failed: {e}") from e
    
    # Save tests
    save_tests(tests)
    
    return tests
