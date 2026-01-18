"""DatumPlan editor - controlled editing with SOE constraint preservation.

SPRINT 3: Enable editing while preserving SOE traceability and audit history.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from services.api.core.plan_immutability import can_modify_plan, ensure_plan_immutable
from services.api.core.storage import get_plan, save_plan, list_plans


def _generate_plan_version(plan: Dict[str, Any]) -> int:
    """Generate next version number for plan."""
    # Get all versions for this plan_id
    quote_id = plan.get("quote_id")
    if not quote_id:
        return 1
    
    existing_plans = list_plans(quote_id=quote_id)
    if not existing_plans:
        return 1
    
    # Find max version
    max_version = 0
    for p in existing_plans:
        version = p.get("version", 1)
        if version > max_version:
            max_version = version
    
    return max_version + 1


def _is_soe_locked_step(step: Dict[str, Any]) -> bool:
    """Check if step is locked by SOE."""
    return (
        step.get("soe_decision_id") is not None
        or step.get("locked_sequence", False)
        or any(
            rule.get("ruleset_version") == 1  # SOE ruleset
            for rule in step.get("source_rules", [])
        )
    )


def _is_soe_locked_test(test: Dict[str, Any]) -> bool:
    """Check if test is locked by SOE."""
    return test.get("soe_decision_id") is not None


def _is_soe_locked_evidence(evidence: Dict[str, Any]) -> bool:
    """Check if evidence requirement is locked by SOE."""
    return evidence.get("soe_decision_id") is not None


def validate_plan_edit(
    original_plan: Dict[str, Any],
    edited_plan: Dict[str, Any],
    allow_overrides: bool = False,
    override_reason: str | None = None,
) -> Tuple[bool, str]:
    """
    Validate that plan edits preserve SOE constraints.
    
    Args:
        original_plan: Original plan version
        edited_plan: Edited plan version
        allow_overrides: Whether to allow SOE constraint overrides
        override_reason: Reason for override (required if allow_overrides=True)
    
    Returns:
        (is_valid, error_message)
    """
    # Cannot edit locked plans
    if original_plan.get("locked"):
        return (
            False,
            "Plan is locked. Create a new revision to make changes.",
        )
    
    # Cannot edit approved plans (they're immutable)
    if original_plan.get("state") == "approved":
        return (
            False,
            "Approved plans are immutable. Create a new version to make changes.",
        )
    
    original_steps = {s["step_id"]: s for s in original_plan.get("steps", [])}
    edited_steps = {s["step_id"]: s for s in edited_plan.get("steps", [])}
    
    # Check for removed SOE-locked steps
    removed_steps = set(original_steps.keys()) - set(edited_steps.keys())
    for step_id in removed_steps:
        step = original_steps[step_id]
        if _is_soe_locked_step(step):
            if not allow_overrides:
                return (
                    False,
                    f"Cannot remove SOE-required step: {step['title']} "
                    f"(Decision ID: {step.get('soe_decision_id')}). "
                    "Override required.",
                )
            if not override_reason or not override_reason.strip():
                return (
                    False,
                    "Override reason required when removing SOE-required steps.",
                )
    
    # Check for reordered locked sequences
    original_sequences = [
        (s["step_id"], s["sequence"], s.get("locked_sequence", False))
        for s in original_plan.get("steps", [])
    ]
    edited_sequences = [
        (s["step_id"], s["sequence"], s.get("locked_sequence", False))
        for s in edited_plan.get("steps", [])
    ]
    
    # Group locked sequences
    locked_groups = []
    current_group = []
    for step_id, seq, is_locked in sorted(original_sequences, key=lambda x: x[1]):
        if is_locked:
            current_group.append((step_id, seq))
        else:
            if current_group:
                locked_groups.append(current_group)
                current_group = []
    if current_group:
        locked_groups.append(current_group)
    
    # Check that locked sequences are preserved
    for group in locked_groups:
        group_step_ids = {s[0] for s in group}
        original_order = [s for s in original_sequences if s[0] in group_step_ids]
        edited_order = [s for s in edited_sequences if s[0] in group_step_ids]
        
        if len(original_order) != len(edited_order):
            if not allow_overrides:
                return (
                    False,
                    f"Cannot modify locked sequence. Steps removed or added. Override required.",
                )
        
        # Check relative order within group
        original_relative = [s[0] for s in sorted(original_order, key=lambda x: x[1])]
        edited_relative = [s[0] for s in sorted(edited_order, key=lambda x: x[1])]
        
        if original_relative != edited_relative:
            if not allow_overrides:
                return (
                    False,
                    f"Cannot reorder locked sequence. Override required.",
                )
            if not override_reason or not override_reason.strip():
                return (
                    False,
                    "Override reason required when reordering locked sequences.",
                )
    
    # Check for removed SOE-locked tests
    original_tests = {t["test_id"]: t for t in original_plan.get("tests", [])}
    edited_tests = {t["test_id"]: t for t in edited_plan.get("tests", [])}
    
    removed_tests = set(original_tests.keys()) - set(edited_tests.keys())
    for test_id in removed_tests:
        test = original_tests[test_id]
        if _is_soe_locked_test(test):
            if not allow_overrides:
                return (
                    False,
                    f"Cannot remove SOE-required test: {test['title']}. Override required.",
                )
            if not override_reason or not override_reason.strip():
                return (
                    False,
                    "Override reason required when removing SOE-required tests.",
                )
    
    # Check for removed SOE-locked evidence
    original_evidence = {
        e["evidence_id"]: e for e in original_plan.get("evidence_intent", [])
    }
    edited_evidence = {
        e["evidence_id"]: e for e in edited_plan.get("evidence_intent", [])
    }
    
    removed_evidence = set(original_evidence.keys()) - set(edited_evidence.keys())
    for evidence_id in removed_evidence:
        evidence = original_evidence[evidence_id]
        if _is_soe_locked_evidence(evidence):
            if not allow_overrides:
                return (
                    False,
                    f"Cannot remove SOE-required evidence: {evidence['evidence_type']}. Override required.",
                )
            if not override_reason or not override_reason.strip():
                return (
                    False,
                    "Override reason required when removing SOE-required evidence.",
                )
    
    return (True, "")


def apply_plan_edit(
    plan: Dict[str, Any],
    edits: Dict[str, Any],
    user_id: str,
    edit_reason: str,
    allow_overrides: bool = False,
    override_reason: str | None = None,
) -> Dict[str, Any]:
    """
    Apply edits to a plan, creating a new version.
    
    Args:
        plan: Original plan
        edits: Edits to apply (partial plan updates)
        user_id: User making the edit
        edit_reason: Reason for edit
        allow_overrides: Whether to allow SOE overrides
        override_reason: Override reason if needed
    
    Returns:
        New plan version with edits applied
    """
    # Create new version
    new_version = _generate_plan_version(plan)
    parent_version = plan.get("version", 1)
    
    # Apply edits
    edited_plan = plan.copy()
    
    # Update editable fields
    if "steps" in edits:
        edited_plan["steps"] = edits["steps"]
    if "tests" in edits:
        edited_plan["tests"] = edits.get("tests", plan.get("tests", []))
    if "evidence_intent" in edits:
        edited_plan["evidence_intent"] = edits.get(
            "evidence_intent", plan.get("evidence_intent", [])
        )
    if "notes" in edits:
        edited_plan["notes"] = edits["notes"]
    if "eee_requirements" in edits:
        edited_plan["eee_requirements"] = edits["eee_requirements"]
    
    # Validate edit
    is_valid, error_msg = validate_plan_edit(
        plan, edited_plan, allow_overrides, override_reason
    )
    if not is_valid:
        raise ValueError(f"Invalid plan edit: {error_msg}")
    
    # Track overrides if any
    overrides = []
    if allow_overrides and override_reason:
        # Detect what was overridden
        original_steps = {s["step_id"]: s for s in plan.get("steps", [])}
        edited_steps = {s["step_id"]: s for s in edited_plan.get("steps", [])}
        
        removed_steps = set(original_steps.keys()) - set(edited_steps.keys())
        for step_id in removed_steps:
            step = original_steps[step_id]
            if _is_soe_locked_step(step):
                overrides.append({
                    "constraint": f"SOE-required step: {step['title']}",
                    "reason": override_reason,
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
    
    # Update metadata
    edited_plan["version"] = new_version
    edited_plan["parent_version"] = parent_version
    edited_plan["state"] = edits.get("state", plan.get("state", "draft"))
    edited_plan["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Add edit metadata
    edited_plan["edit_metadata"] = {
        "edited_by": user_id,
        "edited_at": datetime.now(timezone.utc).isoformat(),
        "edit_reason": edit_reason,
        "overrides": overrides,
    }
    
    return edited_plan


def create_plan_diff(
    plan_v1: Dict[str, Any],
    plan_v2: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate diff between two plan versions.
    
    Returns:
        Diff object with added, removed, and modified items
    """
    diff = {
        "added": {},
        "removed": {},
        "modified": {},
    }
    
    # Compare steps
    steps_v1 = {s["step_id"]: s for s in plan_v1.get("steps", [])}
    steps_v2 = {s["step_id"]: s for s in plan_v2.get("steps", [])}
    
    for step_id, step_v2 in steps_v2.items():
        if step_id not in steps_v1:
            diff["added"]["steps"] = diff["added"].get("steps", [])
            diff["added"]["steps"].append(step_v2)
        else:
            step_v1 = steps_v1[step_id]
            if step_v1 != step_v2:
                diff["modified"]["steps"] = diff["modified"].get("steps", [])
                diff["modified"]["steps"].append({
                    "step_id": step_id,
                    "from": step_v1,
                    "to": step_v2,
                })
    
    for step_id, step_v1 in steps_v1.items():
        if step_id not in steps_v2:
            diff["removed"]["steps"] = diff["removed"].get("steps", [])
            diff["removed"]["steps"].append(step_v1)
    
    # Compare tests
    tests_v1 = {t["test_id"]: t for t in plan_v1.get("tests", [])}
    tests_v2 = {t["test_id"]: t for t in plan_v2.get("tests", [])}
    
    for test_id, test_v2 in tests_v2.items():
        if test_id not in tests_v1:
            diff["added"]["tests"] = diff["added"].get("tests", [])
            diff["added"]["tests"].append(test_v2)
    
    for test_id, test_v1 in tests_v1.items():
        if test_id not in tests_v2:
            diff["removed"]["tests"] = diff["removed"].get("tests", [])
            diff["removed"]["tests"].append(test_v1)
    
    # Compare evidence
    evidence_v1 = {
        e["evidence_id"]: e for e in plan_v1.get("evidence_intent", [])
    }
    evidence_v2 = {
        e["evidence_id"]: e for e in plan_v2.get("evidence_intent", [])
    }
    
    for evidence_id, evidence_v2 in evidence_v2.items():
        if evidence_id not in evidence_v1:
            diff["added"]["evidence"] = diff["added"].get("evidence", [])
            diff["added"]["evidence"].append(evidence_v2)
    
    for evidence_id, evidence_v1 in evidence_v1.items():
        if evidence_id not in evidence_v2:
            diff["removed"]["evidence"] = diff["removed"].get("evidence", [])
            diff["removed"]["evidence"].append(evidence_v1)
    
    return diff
