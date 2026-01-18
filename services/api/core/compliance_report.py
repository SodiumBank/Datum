"""Auditor-Grade Compliance Report Generator (Sprint 5).

Generates formal, auditor-facing compliance reports suitable for
AS9100, ISO 13485, and NASA reviews.
"""

from typing import Any, Dict, List
from datetime import datetime

from services.api.core.storage import get_plan
from services.api.core.compliance_trace import get_plan_compliance_trace


def define_auditor_report_structure() -> Dict[str, Any]:
    """
    Define standard auditor report structure.
    
    Report sections:
    1. Executive Summary
    2. Scope (project, plan, profile stack)
    3. Standards Coverage (matrix of plan steps → standards clauses)
    4. Compliance Traceability (decision lineage)
    5. Deviations and Overrides (explicit listing with justifications)
    6. Approvals Trail (who approved what and when)
    7. Profile Stack (active profiles and versions)
    8. Evidence Requirements (required evidence from SOE)
    9. Audit Metadata (report generation date, report version, hash)
    
    Returns:
        Report structure template
    """
    return {
        "report_version": "1.0.0",
        "sections": [
            {
                "section_id": "executive_summary",
                "title": "Executive Summary",
                "required": True,
                "description": "High-level compliance overview",
            },
            {
                "section_id": "scope",
                "title": "Report Scope",
                "required": True,
                "description": "Project, plan, and profile stack context",
            },
            {
                "section_id": "standards_coverage",
                "title": "Standards Coverage Matrix",
                "required": True,
                "description": "Mapping of plan steps to standards clauses",
            },
            {
                "section_id": "compliance_traceability",
                "title": "Compliance Traceability",
                "required": True,
                "description": "Complete decision lineage from standards to plan steps",
            },
            {
                "section_id": "deviations_overrides",
                "title": "Deviations and Overrides",
                "required": True,
                "description": "Explicit listing of all overrides with justifications",
            },
            {
                "section_id": "approvals_trail",
                "title": "Approvals Trail",
                "required": True,
                "description": "Who approved what and when",
            },
            {
                "section_id": "profile_stack",
                "title": "Standards Profile Stack",
                "required": True,
                "description": "Active profiles, versions, and inheritance",
            },
            {
                "section_id": "evidence_requirements",
                "title": "Evidence Requirements",
                "required": True,
                "description": "Required evidence from SOE decisions",
            },
            {
                "section_id": "audit_metadata",
                "title": "Audit Metadata",
                "required": True,
                "description": "Report generation metadata and integrity hash",
            },
        ],
    }


def generate_clause_coverage_table(compliance_trace: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate clause coverage table mapping plan steps to standards clauses.
    
    Returns matrix of:
    - Step ID / Type / Title
    - Source Standard
    - Standard Clause
    - Standard Section
    - Profile Source
    - SOE Decision ID
    
    Args:
        compliance_trace: Full compliance trace from get_plan_compliance_trace()
    
    Returns:
        List of coverage matrix rows
    """
    coverage_rows: List[Dict[str, Any]] = []
    
    # Process plan steps
    for step in compliance_trace.get("steps", []):
        trace = step.get("compliance_trace", {})
        if trace.get("source_standard") or trace.get("rule_id"):
            coverage_rows.append({
                "entity_type": "step",
                "entity_id": step.get("step_id"),
                "entity_type_detail": step.get("step_type"),
                "entity_title": step.get("step_title"),
                "source_standard": trace.get("source_standard"),
                "standard_clause": trace.get("standard_clause"),
                "standard_section": trace.get("standard_section"),
                "profile_source": trace.get("profile_source"),
                "profile_type": trace.get("profile_type"),
                "soe_decision_id": trace.get("soe_decision_id"),
                "rule_id": trace.get("rule_id"),
                "pack_id": trace.get("pack_id"),
            })
    
    # Process tests
    for test in compliance_trace.get("tests", []):
        trace = test.get("compliance_trace", {})
        if trace.get("profile_source") or trace.get("rule_id"):
            coverage_rows.append({
                "entity_type": "test",
                "entity_id": test.get("test_id"),
                "entity_type_detail": test.get("test_type"),
                "entity_title": test.get("test_title"),
                "source_standard": None,
                "standard_clause": None,
                "standard_section": None,
                "profile_source": trace.get("profile_source"),
                "profile_type": trace.get("profile_type"),
                "soe_decision_id": trace.get("soe_decision_id"),
                "rule_id": trace.get("rule_id"),
                "pack_id": trace.get("pack_id"),
            })
    
    # Process evidence
    for evidence in compliance_trace.get("evidence", []):
        trace = evidence.get("compliance_trace", {})
        if trace.get("profile_source") or trace.get("rule_id"):
            coverage_rows.append({
                "entity_type": "evidence",
                "entity_id": evidence.get("evidence_id"),
                "entity_type_detail": evidence.get("evidence_type"),
                "entity_title": None,
                "source_standard": None,
                "standard_clause": None,
                "standard_section": None,
                "profile_source": trace.get("profile_source"),
                "profile_type": trace.get("profile_type"),
                "soe_decision_id": trace.get("soe_decision_id"),
                "rule_id": trace.get("rule_id"),
                "pack_id": None,
            })
    
    return coverage_rows


def generate_deviations_overrides_section(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate deviations and overrides section.
    
    Explicitly lists:
    - All plan overrides (override_reason, override_by, override_at)
    - Steps with overrides (including SOE-locked step overrides)
    - Approval history (rejected then approved, etc.)
    
    Args:
        plan: DatumPlan object
    
    Returns:
        Deviations and overrides section data
    """
    overrides: List[Dict[str, Any]] = []
    
    # Plan-level overrides
    if plan.get("override_reason"):
        overrides.append({
            "level": "plan",
            "entity_id": plan.get("id"),
            "override_reason": plan.get("override_reason"),
            "override_by": plan.get("override_by"),
            "override_at": plan.get("override_at"),
            "parent_plan_id": plan.get("parent_version"),
            "version": plan.get("version"),
        })
    
    # Step-level overrides (steps that were SOE-locked but overridden)
    for step in plan.get("steps", []):
        # Check if step has override metadata or is marked as overridden
        if step.get("override_reason") or step.get("is_overridden"):
            overrides.append({
                "level": "step",
                "entity_id": step.get("step_id"),
                "entity_type": step.get("type"),
                "entity_title": step.get("title"),
                "override_reason": step.get("override_reason"),
                "override_by": step.get("override_by"),
                "override_at": step.get("override_at"),
                "soe_decision_id": step.get("soe_decision_id"),
                "soe_locked": step.get("soe_locked", False),
            })
    
    return {
        "override_count": len(overrides),
        "overrides": overrides,
        "has_deviations": len(overrides) > 0,
    }


def generate_approvals_trail(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate approvals trail.
    
    Returns chronological list of approval events:
    - Submission (who, when)
    - Approvals (who, when, version)
    - Rejections (who, when, reason)
    - Override approvals (who, when, reason)
    
    Args:
        plan: DatumPlan object
    
    Returns:
        List of approval events in chronological order
    """
    events: List[Dict[str, Any]] = []
    
    # Submission
    if plan.get("state") != "draft":
        # Note: We don't store explicit "submitted" timestamp, infer from state
        events.append({
            "event_type": "submitted",
            "status": "submitted",
            "timestamp": plan.get("updated_at"),  # Approximation
        })
    
    # Approval
    if plan.get("approved_by"):
        events.append({
            "event_type": "approved",
            "approved_by": plan.get("approved_by"),
            "approved_at": plan.get("approved_at"),
            "version": plan.get("version"),
        })
    
    # Rejection
    if plan.get("rejected_by"):
        events.append({
            "event_type": "rejected",
            "rejected_by": plan.get("rejected_by"),
            "rejected_at": plan.get("rejected_at"),
        })
    
    # Override approval
    if plan.get("override_by"):
        events.append({
            "event_type": "override_approved",
            "override_by": plan.get("override_by"),
            "override_at": plan.get("override_at"),
            "override_reason": plan.get("override_reason"),
        })
    
    # Sort by timestamp
    events.sort(key=lambda e: e.get("approved_at") or e.get("rejected_at") or e.get("override_at") or e.get("timestamp") or "")
    
    return events


def build_compliance_report_data(plan_id: str) -> Dict[str, Any]:
    """
    Build complete compliance report data structure.
    
    Assembles all sections into a single report structure ready for rendering.
    
    Args:
        plan_id: Plan ID to generate report for
    
    Returns:
        Complete report data structure
    """
    # Get plan and compliance trace
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError(f"Plan not found: {plan_id}")
    
    # Verify plan is approved (reports only from approved plans)
    if plan.get("state") != "approved":
        raise ValueError(f"Plan must be approved to generate compliance report. Current status: {plan.get('state')}")
    
    compliance_trace = get_plan_compliance_trace(plan_id)
    
    # Build report structure
    report_structure = define_auditor_report_structure()
    
    # Generate sections
    clause_coverage = generate_clause_coverage_table(compliance_trace)
    deviations_overrides = generate_deviations_overrides_section(plan)
    approvals_trail = generate_approvals_trail(plan)
    
    # Build report data
    report_data = {
        "report_metadata": {
            "report_version": report_structure["report_version"],
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "plan_id": plan_id,
            "plan_version": plan.get("version"),
            "report_type": "compliance_audit",
        },
        "executive_summary": {
            "plan_id": plan_id,
            "plan_version": plan.get("version"),
            "status": plan.get("state"),
            "total_steps": len(plan.get("steps", [])),
            "total_tests": len(plan.get("tests", [])),
            "total_evidence": len(plan.get("evidence_intent", [])),
            "profile_stack_count": len(compliance_trace.get("profile_stack", [])),
            "override_count": deviations_overrides["override_count"],
            "has_deviations": deviations_overrides["has_deviations"],
        },
        "scope": {
            "plan_id": plan_id,
            "plan_version": plan.get("version"),
            "quote_id": plan.get("quote_id"),
            "org_id": plan.get("org_id"),
            "design_id": plan.get("design_id"),
            "profile_stack": compliance_trace.get("profile_stack", []),
            "soe_run_id": plan.get("soe_run_id"),
        },
        "standards_coverage": {
            "coverage_table": clause_coverage,
            "total_entities": len(clause_coverage),
            "standards_covered": list(set(row.get("source_standard") for row in clause_coverage if row.get("source_standard"))),
        },
        "compliance_traceability": {
            "steps": compliance_trace.get("steps", []),
            "tests": compliance_trace.get("tests", []),
            "evidence": compliance_trace.get("evidence", []),
        },
        "deviations_overrides": deviations_overrides,
        "approvals_trail": approvals_trail,
        "profile_stack": {
            "profiles": compliance_trace.get("profile_stack", []),
            "profile_count": len(compliance_trace.get("profile_stack", [])),
        },
        "evidence_requirements": {
            "evidence_items": compliance_trace.get("evidence", []),
            "evidence_count": len(compliance_trace.get("evidence", [])),
        },
    }
    
    return report_data
