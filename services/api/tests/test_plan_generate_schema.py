"""Regression test: Plan generation produces schema-valid plans (Sprint 7)."""

import pytest
from services.api.core.plan_generator import generate_plan
from services.api.core.storage import save_quote, get_quote
from services.api.core.schema_validation import validate_schema


@pytest.fixture
def sample_quote():
    """Create a sample quote for plan generation."""
    quote = {
        "id": "quote_test_schema_001",
        "org_id": "org_test_001",
        "design_id": "design_test_001",
        "tier": "TIER_1",
        "revision_id": "rev_A",
        "quote_version": 1,
        "inputs_fingerprint": "a" * 64,
        "lead_time_days": 14,
        "cost_breakdown": {
            "total": 1000.0,
            "currency": "USD",
            "lines": [
                {"code": "PCB_FAB", "label": "PCB Fabrication", "amount": 500.0},
            ],
        },
        "risk_factors": [],
        "assumptions": {"assembly_sides": ["TOP"]},
        "status": "LOCKED",
        "created_at": "2026-01-01T00:00:00Z",
    }
    save_quote(quote)
    return quote


def test_generate_plan_produces_valid_schema(sample_quote):
    """
    Regression test: POST /plans/generate produces a plan that validates against schemas (Sprint 7).
    
    This ensures plan_generator fixes (removing None values, populating source_rules)
    result in schema-compliant plans.
    """
    quote_id = sample_quote["id"]
    
    # Generate plan
    plan = generate_plan(
        quote_id=quote_id,
        ruleset_version=1,
        org_id=sample_quote["org_id"],
        design_id=sample_quote["design_id"],
    )
    
    # Verify plan structure
    assert plan is not None, "Plan should not be None"
    assert "id" in plan, "Plan must have id"
    assert "steps" in plan, "Plan must have steps"
    
    # Validate against schema
    try:
        validate_schema(plan, "datum_plan.schema.json")
    except Exception as e:
        pytest.fail(f"Plan schema validation failed: {e}")
    
    # Verify steps are schema-compliant
    for step in plan.get("steps", []):
        # Check source_rules has at least one entry (schema requires minItems: 1)
        assert "source_rules" in step, "Step must have source_rules"
        assert len(step["source_rules"]) > 0, "source_rules must have at least one entry (minItems: 1)"
        
        # Check no None values for optional object fields (parameters/acceptance should be omitted if None)
        if "parameters" in step:
            assert step["parameters"] is not None, "If parameters present, must not be None"
            assert isinstance(step["parameters"], dict), "parameters must be dict if present"
        
        if "acceptance" in step:
            assert step["acceptance"] is not None, "If acceptance present, must not be None"
            assert isinstance(step["acceptance"], dict), "acceptance must be dict if present"
        
        # Validate step against step schema
        try:
            validate_schema(step, "datum_plan_step.schema.json")
        except Exception as e:
            pytest.fail(f"Step {step.get('step_id')} schema validation failed: {e}")


def test_generate_plan_steps_have_source_rules(sample_quote):
    """Ensure all steps have source_rules populated (Sprint 7 fix)."""
    quote_id = sample_quote["id"]
    
    plan = generate_plan(
        quote_id=quote_id,
        ruleset_version=1,
        org_id=sample_quote["org_id"],
        design_id=sample_quote["design_id"],
    )
    
    steps = plan.get("steps", [])
    assert len(steps) > 0, "Plan should have at least one step"
    
    for step in steps:
        assert "source_rules" in step, f"Step {step.get('step_id')} missing source_rules"
        assert len(step["source_rules"]) > 0, f"Step {step.get('step_id')} has empty source_rules"
