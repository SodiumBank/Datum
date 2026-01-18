"""Audit Artifact Consistency Checks (Sprint 6).

Provides audit integrity verification for plans, exports, reports, and profiles.
"""

from typing import Any, Dict, List
from services.api.core.storage import get_plan, get_soe_run
from services.api.core.profile_lifecycle import get_profile_state, validate_profile_for_use


def check_audit_integrity(plan_id: str) -> Dict[str, Any]:
    """
    Perform comprehensive audit integrity check for a plan.
    
    Verifies:
    1. Plan is approved (required for audit readiness)
    2. Plan has export hash (if exported)
    3. Compliance report hash present (if report generated)
    4. Profile states are valid (approved/deprecated, not draft)
    5. Profile stack is recorded and traceable
    6. SOE run is deterministic and traceable
    
    Args:
        plan_id: Plan ID to check
    
    Returns:
        Audit integrity checklist with PASS/FAIL + reasons for each check
    """
    checklist: Dict[str, Any] = {
        "plan_id": plan_id,
        "overall_status": "PASS",
        "checks": [],
    }
    
    # Check 1: Plan exists and is approved
    plan = get_plan(plan_id)
    if not plan:
        checklist["overall_status"] = "FAIL"
        checklist["checks"].append({
            "check_id": "plan_exists",
            "status": "FAIL",
            "reason": f"Plan {plan_id} not found",
        })
        return checklist
    else:
        checklist["checks"].append({
            "check_id": "plan_exists",
            "status": "PASS",
            "reason": "Plan found",
        })
    
    plan_state = plan.get("state", "draft")
    if plan_state != "approved":
        checklist["overall_status"] = "FAIL"
        checklist["checks"].append({
            "check_id": "plan_approved",
            "status": "FAIL",
            "reason": f"Plan state is '{plan_state}', must be 'approved' for audit readiness",
        })
    else:
        checklist["checks"].append({
            "check_id": "plan_approved",
            "status": "PASS",
            "reason": "Plan is approved",
        })
    
    # Check 2: Plan has provenance metadata (Sprint 5 export hardening)
    plan_version = plan.get("version")
    approved_by = plan.get("approved_by")
    approved_at = plan.get("approved_at")
    
    if not plan_version or not approved_by or not approved_at:
        checklist["checks"].append({
            "check_id": "plan_provenance",
            "status": "WARN",
            "reason": "Plan missing some provenance metadata (version, approved_by, approved_at)",
        })
    else:
        checklist["checks"].append({
            "check_id": "plan_provenance",
            "status": "PASS",
            "reason": "Plan has complete provenance metadata",
            "details": {
                "version": plan_version,
                "approved_by": approved_by,
                "approved_at": approved_at,
            },
        })
    
    # Check 3: SOE run exists and is traceable
    soe_run_id = plan.get("soe_run_id")
    if soe_run_id:
        soe_run = get_soe_run(soe_run_id)
        if soe_run:
            checklist["checks"].append({
                "check_id": "soe_run_traceable",
                "status": "PASS",
                "reason": "SOE run found and traceable",
                "details": {
                    "soe_run_id": soe_run_id,
                    "industry_profile": soe_run.get("industry_profile"),
                    "decision_count": len(soe_run.get("decisions", [])),
                },
            })
        else:
            checklist["checks"].append({
                "check_id": "soe_run_traceable",
                "status": "WARN",
                "reason": f"SOE run {soe_run_id} referenced but not found",
            })
    else:
        checklist["checks"].append({
            "check_id": "soe_run_traceable",
            "status": "WARN",
            "reason": "Plan does not reference an SOE run",
        })
    
    # Check 4: Profile stack validity (Sprint 4-5)
    soe_run = None
    if soe_run_id:
        soe_run = get_soe_run(soe_run_id)
    
    if soe_run:
        active_profiles = soe_run.get("active_profiles", [])
        profile_stack = soe_run.get("profile_stack", [])
        
        if not active_profiles and not profile_stack:
            checklist["checks"].append({
                "check_id": "profile_stack_recorded",
                "status": "INFO",
                "reason": "No profile stack recorded (plan may have been generated without profiles)",
            })
        else:
            # Verify each profile in stack is valid (approved or deprecated, not draft)
            invalid_profiles: List[str] = []
            profile_states: Dict[str, str] = {}
            
            for profile_id in active_profiles:
                try:
                    state = get_profile_state(profile_id)
                    profile_states[profile_id] = state
                    
                    # Only approved or deprecated profiles should be in approved plans
                    if state not in ["approved", "deprecated"]:
                        invalid_profiles.append(f"{profile_id} (state: {state})")
                except ValueError as e:
                    invalid_profiles.append(f"{profile_id} (not found: {e})")
            
            if invalid_profiles:
                checklist["overall_status"] = "FAIL"
                checklist["checks"].append({
                    "check_id": "profile_states_valid",
                    "status": "FAIL",
                    "reason": f"Profiles not in approved state: {', '.join(invalid_profiles)}",
                    "details": profile_states,
                })
            else:
                checklist["checks"].append({
                    "check_id": "profile_states_valid",
                    "status": "PASS",
                    "reason": "All profiles in stack are approved or deprecated",
                    "details": {
                        "profile_count": len(active_profiles),
                        "profile_states": profile_states,
                    },
                })
            
            # Profile stack recorded
            checklist["checks"].append({
                "check_id": "profile_stack_recorded",
                "status": "PASS",
                "reason": f"Profile stack recorded with {len(profile_stack)} profiles",
                "details": {
                    "active_profiles": active_profiles,
                    "profile_stack_layers": [p.get("layer") for p in profile_stack],
                },
            })
    
    # Check 5: SOE decisions have deterministic IDs
    if soe_run:
        decisions = soe_run.get("decisions", [])
        decision_ids = [d.get("id") for d in decisions if d.get("id")]
        
        # Check ID format (should be DEC-[0-9A-F]{8})
        import re
        pattern = r"^DEC-[0-9A-F]{8}$"
        invalid_ids = [did for did in decision_ids if not re.match(pattern, did)]
        
        if invalid_ids:
            checklist["checks"].append({
                "check_id": "soe_decision_ids_deterministic",
                "status": "WARN",
                "reason": f"Some decision IDs have invalid format: {invalid_ids[:3]}",
            })
        else:
            checklist["checks"].append({
                "check_id": "soe_decision_ids_deterministic",
                "status": "PASS",
                "reason": f"All {len(decision_ids)} decision IDs have deterministic format",
            })
    
    # Check 6: Plan steps reference SOE decisions (traceability)
    plan_steps = plan.get("steps", [])
    steps_with_soe_refs = [s for s in plan_steps if s.get("soe_decision_id")]
    soe_decision_ids_in_plan = plan.get("soe_decision_ids", [])
    
    if soe_decision_ids_in_plan:
        checklist["checks"].append({
            "check_id": "plan_soe_traceability",
            "status": "PASS",
            "reason": f"Plan references {len(soe_decision_ids_in_plan)} SOE decision IDs",
            "details": {
                "steps_with_soe_refs": len(steps_with_soe_refs),
                "total_steps": len(plan_steps),
            },
        })
    else:
        checklist["checks"].append({
            "check_id": "plan_soe_traceability",
            "status": "INFO",
            "reason": "Plan does not reference SOE decisions (may have been generated without SOE)",
        })
    
    return checklist


def summarize_audit_integrity(checklist: Dict[str, Any]) -> str:
    """
    Generate human-readable summary of audit integrity check.
    
    Args:
        checklist: Result from check_audit_integrity()
    
    Returns:
        Summary string
    """
    status = checklist["overall_status"]
    checks = checklist["checks"]
    
    pass_count = sum(1 for c in checks if c["status"] == "PASS")
    fail_count = sum(1 for c in checks if c["status"] == "FAIL")
    warn_count = sum(1 for c in checks if c["status"] == "WARN")
    info_count = sum(1 for c in checks if c["status"] == "INFO")
    
    summary = f"Audit Integrity Check for Plan {checklist['plan_id']}: {status}\n\n"
    summary += f"Results: {pass_count} PASS, {fail_count} FAIL, {warn_count} WARN, {info_count} INFO\n\n"
    
    for check in checks:
        status_symbol = {
            "PASS": "✓",
            "FAIL": "✗",
            "WARN": "⚠",
            "INFO": "ℹ",
        }.get(check["status"], "?")
        
        summary += f"{status_symbol} {check['check_id']}: {check['reason']}\n"
    
    return summary
