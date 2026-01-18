"""Regression tests to ensure Sprint 2 determinism guarantees remain intact (Sprint 3)."""

import pytest
from services.api.core.plan_generator import generate_plan
from services.api.core.soe_engine import evaluate_soe
from services.api.core.storage import save_quote, get_quote


def test_soe_determinism_unchanged():
    """Test that SOE still produces deterministic outputs (Sprint 2 guarantee)."""
    # Same inputs should produce same SOERun
    inputs = {
        "processes": ["SMT", "REFLOW", "CONFORMAL_COAT"],
        "tests_requested": ["FUNCTIONAL"],
        "materials": ["EPOXY_3M_SCOTCHWELD_2216"],
        "bom_risk_flags": ["LONG_LEAD_EEE"],
    }
    
    soe_run_1 = evaluate_soe(
        industry_profile="space",
        inputs=inputs,
        hardware_class="flight",
    )
    
    soe_run_2 = evaluate_soe(
        industry_profile="space",
        inputs=inputs,
        hardware_class="flight",
    )
    
    # Decision IDs should be identical (deterministic)
    decisions_1 = {d["id"] for d in soe_run_1.get("decisions", [])}
    decisions_2 = {d["id"] for d in soe_run_2.get("decisions", [])}
    
    assert decisions_1 == decisions_2


def test_plan_generation_determinism_unchanged():
    """Test that plan generation from SOE is still deterministic (Sprint 2 guarantee)."""
    # Create quote
    quote_id = "quote_determinism_test"
    quote = {
        "id": quote_id,
        "org_id": "org_test_001",
        "design_id": "design_test_001",
        "revision_id": "rev_test_001",
        "quote_version": 1,
        "tier": "TIER_1",
        "assumptions": {
            "assembly_sides": ["TOP"],
        },
    }
    save_quote(quote)
    
    # Generate SOERun
    soe_inputs = {
        "processes": ["SMT", "REFLOW"],
        "tests_requested": ["FUNCTIONAL"],
        "materials": [],
        "bom_risk_flags": [],
    }
    soe_run = evaluate_soe(
        industry_profile="space",
        inputs=soe_inputs,
        hardware_class="flight",
    )
    
    # Generate plan twice
    plan_1 = generate_plan(
        quote_id=quote_id,
        soe_run=soe_run,
        org_id="org_test_001",
        design_id="design_test_001",
    )
    
    plan_2 = generate_plan(
        quote_id=quote_id,
        soe_run=soe_run,
        org_id="org_test_001",
        design_id="design_test_001",
    )
    
    # Structure should match (IDs may differ but structure should be identical)
    assert len(plan_1["steps"]) == len(plan_2["steps"])
    assert len(plan_1.get("tests", [])) == len(plan_2.get("tests", []))
    
    # Step types and sequences should match
    steps_1 = sorted(plan_1["steps"], key=lambda s: s["sequence"])
    steps_2 = sorted(plan_2["steps"], key=lambda s: s["sequence"])
    
    for s1, s2 in zip(steps_1, steps_2):
        assert s1["type"] == s2["type"]
        assert s1["sequence"] == s2["sequence"]
        assert s1["required"] == s2["required"]
        assert s1["locked_sequence"] == s2["locked_sequence"]
        
        # SOE references should match
        if s1.get("soe_decision_id"):
            assert s1["soe_decision_id"] == s2.get("soe_decision_id")


def test_initial_plan_state_is_draft():
    """Test that newly generated plans start in draft state (Sprint 3)."""
    quote_id = "quote_draft_test"
    quote = {
        "id": quote_id,
        "org_id": "org_test_001",
        "design_id": "design_test_001",
        "revision_id": "rev_test_001",
        "quote_version": 1,
        "tier": "TIER_1",
        "assumptions": {},
    }
    save_quote(quote)
    
    plan = generate_plan(
        quote_id=quote_id,
        soe_run=None,
        org_id="org_test_001",
        design_id="design_test_001",
    )
    
    assert plan["state"] == "draft"
    assert plan["version"] == 1
    assert plan["locked"] is False
