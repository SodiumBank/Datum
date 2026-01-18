"""Rules engine for evaluating DatumRule triggers against extracted features."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, TypedDict

ROOT = Path(__file__).resolve().parents[3]
RULES_DIR = ROOT / "rules"
SCHEMAS = ROOT / "schemas"


class RuleTrace(TypedDict):
    """Trace record for a matched rule."""
    rule_id: str
    ruleset_version: int
    justification: str
    category: str
    severity: str


class FeatureContext(TypedDict, total=False):
    """Context for evaluating rule triggers."""
    board_metrics: Dict[str, Any]
    bom_items: List[Dict[str, Any]] | None
    quote: Dict[str, Any] | None
    assumptions: Dict[str, Any] | None
    gerber_files: List[Dict[str, Any]] | None


class DatumRule(TypedDict):
    """DatumRule structure."""
    rule_id: str
    category: str
    tier_required: str
    severity: str
    trigger: str
    actions: List[Dict[str, Any]]
    justification: str
    ruleset_version: int


def _load_ruleset(ruleset_version: int = 1) -> List[DatumRule]:
    """Load rules from JSON file for a given ruleset version."""
    rules_file = RULES_DIR / f"ruleset_v{ruleset_version}.json"
    
    if not rules_file.exists():
        # Return empty ruleset if file doesn't exist
        return []
    
    try:
        data = json.loads(rules_file.read_text(encoding="utf-8"))
        rules = data.get("rules", [])
        
        # Ensure ruleset_version is set on each rule
        for rule in rules:
            rule["ruleset_version"] = ruleset_version
        
        return rules
    except Exception as e:
        raise ValueError(f"Failed to load ruleset v{ruleset_version}: {e}")


def _evaluate_expression(expr: str, context: FeatureContext) -> bool:
    """
    Evaluate a trigger expression against feature context.
    
    Supports:
    - Boolean operators: OR, AND, NOT
    - Comparisons: >=, <=, ==, !=, >, <
    - String operations: in, not in (for lists/arrays)
    - Feature access: dot notation (e.g., board_metrics.layers)
    
    Example expressions:
    - "board_metrics.layers >= 4"
    - "bom_items.package in ('BGA', 'QFN')"
    - "assumptions.compliance_mode == 'NASA' OR assumptions.coating_required == True"
    """
    if not expr or not expr.strip():
        return False
    
    # Normalize expression
    expr = expr.strip()
    
    # Replace common operators
    expr = expr.replace(" AND ", " and ")
    expr = expr.replace(" OR ", " or ")
    expr = expr.replace(" NOT ", " not ")
    
    # Safe evaluation - build a safe evaluation context
    safe_context: Dict[str, Any] = {}
    
    # Add board_metrics if available
    if context.get("board_metrics"):
        for key, value in context["board_metrics"].items():
            safe_context[f"board_metrics.{key}"] = value
            # Also add at root level for convenience
            safe_context[key] = value
    
    # Add assumptions if available
    if context.get("assumptions"):
        for key, value in context["assumptions"].items():
            safe_context[f"assumptions.{key}"] = value
            safe_context[key] = value
    
    # Add BOM item features (check any item)
    if context.get("bom_items"):
        bom_items = context["bom_items"]
        # Extract unique packages
        packages = set()
        has_eee = False
        max_lead_time = 0
        
        for item in bom_items:
            if "package" in item:
                packages.add(item["package"].upper())
            if item.get("is_eee"):
                has_eee = True
            if "lead_time_weeks" in item:
                lead_time = item.get("lead_time_weeks", 0)
                if isinstance(lead_time, (int, float)):
                    max_lead_time = max(max_lead_time, lead_time)
        
        safe_context["bom_items.packages"] = list(packages)
        safe_context["bom_items.has_eee"] = has_eee
        safe_context["bom_items.max_lead_time_weeks"] = max_lead_time
    
    # Add quote features
    if context.get("quote"):
        quote = context["quote"]
        safe_context["quote.tier"] = quote.get("tier")
        safe_context["quote.quantity"] = quote.get("quantity", 1)
    
    # Helper function to check if a value is in a list
    def value_in(value: Any, items: Any) -> bool:
        if isinstance(items, str):
            # Parse list-like strings: "('BGA', 'QFN')" or "['BGA', 'QFN']"
            items_str = items.strip()
            if items_str.startswith("(") and items_str.endswith(")"):
                items_str = items_str[1:-1]
            elif items_str.startswith("[") and items_str.endswith("]"):
                items_str = items_str[1:-1]
            items = [item.strip().strip("'\"") for item in items_str.split(",")]
        if not isinstance(items, (list, tuple, set)):
            return False
        return str(value).upper() in [str(item).upper() for item in items]
    
    safe_context["__value_in__"] = value_in
    
    # Pattern matching for common expressions
    # Match: "x in (a, b, c)" or "x in ['a', 'b', 'c']"
    in_pattern = r'(\w+(?:\.\w+)*)\s+in\s+([(\[].*?[)\]])'
    def replace_in(match):
        var_name = match.group(1)
        items_str = match.group(2)
        return f"__value_in__({var_name}, {items_str})"
    
    expr = re.sub(in_pattern, replace_in, expr, flags=re.IGNORECASE)
    
    # Pattern matching for: "package in (BGA, QFN)"
    # Convert to: "any('BGA' in bom_items.packages, 'QFN' in bom_items.packages)"
    package_in_pattern = r'package\s+in\s+\(([^)]+)\)'
    def replace_package_in(match):
        packages_str = match.group(1)
        packages = [p.strip().strip("'\"") for p in packages_str.split(",")]
        checks = [f"__value_in__('{p}', bom_items.packages)" for p in packages]
        return f"({' or '.join(checks)})"
    
    expr = re.sub(package_in_pattern, replace_package_in, expr, flags=re.IGNORECASE)
    
    # Safe evaluation using eval with limited context
    try:
        # Replace common boolean operators
        expr = expr.replace("True", "True").replace("False", "False")
        
        # Evaluate
        result = eval(expr, {"__builtins__": {}}, safe_context)
        return bool(result) if result is not None else False
    except Exception as e:
        # If evaluation fails, return False and log (in production, log to logger)
        print(f"Warning: Failed to evaluate expression '{expr}': {e}")
        return False


def evaluate_rules(context: FeatureContext, ruleset_version: int = 1, tier: str = "TIER_1") -> List[RuleTrace]:
    """
    Evaluate all rules in a ruleset against the feature context.
    
    Args:
        context: Feature context (board_metrics, bom_items, quote, assumptions)
        ruleset_version: Version of ruleset to load
        tier: Current tier (only rules with tier_required <= tier are evaluated)
    
    Returns:
        List of RuleTrace records for matched rules
    """
    # Load ruleset
    rules = _load_ruleset(ruleset_version)
    
    # Tier mapping for comparison
    tier_order = {"TIER_1": 1, "TIER_2": 2, "TIER_3": 3}
    current_tier_order = tier_order.get(tier, 1)
    
    traces: List[RuleTrace] = []
    
    for rule in rules:
        # Check tier requirement
        rule_tier = rule.get("tier_required", "TIER_1")
        rule_tier_order = tier_order.get(rule_tier, 1)
        
        if rule_tier_order > current_tier_order:
            # Skip rules requiring higher tier
            continue
        
        # Evaluate trigger
        trigger = rule.get("trigger", "")
        if _evaluate_expression(trigger, context):
            # Rule matched - add to trace
            trace: RuleTrace = {
                "rule_id": rule["rule_id"],
                "ruleset_version": rule.get("ruleset_version", ruleset_version),
                "justification": rule.get("justification", ""),
                "category": rule.get("category", ""),
                "severity": rule.get("severity", "MEDIUM"),
            }
            traces.append(trace)
    
    return traces


def load_ruleset_info(ruleset_version: int = 1) -> Dict[str, Any]:
    """Load ruleset metadata."""
    rules_file = RULES_DIR / f"ruleset_v{ruleset_version}.json"
    
    if not rules_file.exists():
        return {
            "ruleset_version": ruleset_version,
            "rule_count": 0,
            "rules": [],
        }
    
    try:
        data = json.loads(rules_file.read_text(encoding="utf-8"))
        rules = data.get("rules", [])
        
        return {
            "ruleset_version": ruleset_version,
            "rule_count": len(rules),
            "rules": rules,
        }
    except Exception as e:
        raise ValueError(f"Failed to load ruleset v{ruleset_version}: {e}")
