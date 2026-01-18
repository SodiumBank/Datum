"""Compliance Traceability - map plan steps to standards and clauses (Sprint 4)."""

from typing import Any, Dict, List

from services.api.core.storage import get_plan, get_soe_run
from services.api.core.profile_stack import load_profile, resolve_profile_stack


def build_compliance_trace_for_step(
    step: Dict[str, Any],
    soe_run: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Build compliance traceability for a plan step.
    
    Maps step to:
    - Source standard and clause
    - Profile source and layer
    - SOE decision ID
    - Rule ID and pack
    
    Args:
        step: Plan step
        soe_run: SOERun object (if available)
    
    Returns:
        Compliance trace object
    """
    trace: Dict[str, Any] = {}
    
    # Get SOE decision if step has one
    soe_decision_id = step.get("soe_decision_id")
    if soe_decision_id and soe_run:
        decisions = soe_run.get("decisions", [])
        decision = next((d for d in decisions if d.get("id") == soe_decision_id), None)
        
        if decision:
            # Extract profile source from decision
            profile_source = decision.get("profile_source")
            profile_type = decision.get("profile_type")
            profile_layer = decision.get("profile_layer")
            clause_reference = decision.get("clause_reference")
            
            trace["soe_decision_id"] = soe_decision_id
            trace["profile_source"] = profile_source
            trace["profile_type"] = profile_type
            trace["profile_layer"] = profile_layer
            trace["clause_reference"] = clause_reference
            
            # Get source standard from profile
            if profile_source:
                try:
                    profile = load_profile(profile_source)
                    source_standards = profile.get("source_standards", [])
                    if source_standards and clause_reference:
                        # Find matching standard by clause
                        matching_std = next(
                            (s for s in source_standards if s.get("clause") == clause_reference),
                            source_standards[0] if source_standards else None
                        )
                        if matching_std:
                            trace["source_standard"] = matching_std.get("standard_id")
                            trace["standard_clause"] = matching_std.get("clause")
                            trace["standard_section"] = matching_std.get("section")
                except ValueError:
                    # Profile not found - skip
                    pass
            
            # Get rule ID and pack from decision why
            why = decision.get("why", {})
            trace["rule_id"] = why.get("rule_id")
            trace["pack_id"] = why.get("pack_id")
            trace["citations"] = why.get("citations", [])
    
    # If no SOE decision, check source_rules
    if not trace.get("rule_id") and step.get("source_rules"):
        source_rules = step.get("source_rules", [])
        if source_rules:
            rule = source_rules[0]
            trace["rule_id"] = rule.get("rule_id")
            trace["justification"] = rule.get("justification")
    
    return trace


def get_plan_compliance_trace(plan_id: str) -> Dict[str, Any]:
    """
    Get full compliance traceability for a plan.
    
    Returns:
        Compliance trace object with step mappings and profile stack
    """
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")
    
    # Get SOERun if available
    soe_run_id = plan.get("soe_run_id")
    soe_run = None
    if soe_run_id:
        soe_run = get_soe_run(soe_run_id)
    
    # Get profile stack from SOERun
    profile_stack: List[Dict[str, Any]] = []
    if soe_run:
        active_profiles = soe_run.get("active_profiles", [])
        if active_profiles:
            resolved_profiles, errors = resolve_profile_stack(active_profiles)
            if not errors:
                profile_stack = [
                    {
                        "profile_id": p["profile_id"],
                        "profile_type": p["profile_type"],
                        "name": p["name"],
                        "layer": i,
                        "source_standards": p.get("source_standards", []),
                    }
                    for i, p in enumerate(resolved_profiles)
                ]
    
    # Build traces for all steps
    step_traces: List[Dict[str, Any]] = []
    for step in plan.get("steps", []):
        trace = build_compliance_trace_for_step(step, soe_run)
        step_traces.append({
            "step_id": step.get("step_id"),
            "step_type": step.get("type"),
            "step_title": step.get("title"),
            "compliance_trace": trace,
        })
    
    # Build traces for tests
    test_traces: List[Dict[str, Any]] = []
    for test in plan.get("tests", []):
        trace = {}
        soe_decision_id = test.get("soe_decision_id")
        if soe_decision_id and soe_run:
            decisions = soe_run.get("decisions", [])
            decision = next((d for d in decisions if d.get("id") == soe_decision_id), None)
            if decision:
                trace = {
                    "soe_decision_id": soe_decision_id,
                    "profile_source": decision.get("profile_source"),
                    "profile_type": decision.get("profile_type"),
                    "rule_id": decision.get("why", {}).get("rule_id"),
                    "pack_id": decision.get("why", {}).get("pack_id"),
                }
        test_traces.append({
            "test_id": test.get("test_id"),
            "test_type": test.get("test_type"),
            "test_title": test.get("title"),
            "compliance_trace": trace,
        })
    
    # Build traces for evidence
    evidence_traces: List[Dict[str, Any]] = []
    for evidence in plan.get("evidence_intent", []):
        trace = {}
        soe_decision_id = evidence.get("soe_decision_id")
        if soe_decision_id and soe_run:
            decisions = soe_run.get("decisions", [])
            decision = next((d for d in decisions if d.get("id") == soe_decision_id), None)
            if decision:
                trace = {
                    "soe_decision_id": soe_decision_id,
                    "profile_source": decision.get("profile_source"),
                    "profile_type": decision.get("profile_type"),
                    "rule_id": decision.get("why", {}).get("rule_id"),
                }
        evidence_traces.append({
            "evidence_id": evidence.get("evidence_id"),
            "evidence_type": evidence.get("evidence_type"),
            "compliance_trace": trace,
        })
    
    return {
        "plan_id": plan_id,
        "plan_version": plan.get("version"),
        "profile_stack": profile_stack,
        "steps": step_traces,
        "tests": test_traces,
        "evidence": evidence_traces,
    }
