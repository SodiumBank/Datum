"""Tests for DatumPlan optimization (Sprint 3)."""

import pytest
from services.api.core.plan_optimizer import (
    optimize_plan_steps,
    generate_optimization_summary,
)
from services.api.core.storage import save_plan


@pytest.fixture
def plan_with_unlocked_steps():
    """Create a plan with unlocked steps for optimization."""
    return {
        "id": "plan_test_opt",
        "org_id": "org_test_001",
        "design_id": "design_test_001",
        "revision_id": "rev_test_001",
        "quote_id": "quote_test_001",
        "quote_version": 1,
        "plan_revision": "A",
        "locked": False,
        "version": 1,
        "state": "draft",
        "steps": [
            {
                "step_id": "step_001",
                "type": "FAB",
                "title": "PCB Fabrication",
                "sequence": 1,
                "required": True,
                "locked_sequence": False,
            },
            {
                "step_id": "step_002",
                "type": "SMT",
                "title": "SMT Assembly",
                "sequence": 2,
                "required": True,
                "locked_sequence": False,
            },
            {
                "step_id": "step_003",
                "type": "INSPECT",
                "title": "Inspection",
                "sequence": 3,
                "required": True,
                "locked_sequence": False,
            },
        ],
        "tests": [],
        "evidence_intent": [],
        "created_at": "2026-01-18T00:00:00Z",
        "updated_at": "2026-01-18T00:00:00Z",
    }


def test_optimize_plan_creates_new_version(plan_with_unlocked_steps):
    """Test that optimization creates a new version."""
    save_plan(plan_with_unlocked_steps)
    
    optimized = optimize_plan_steps(plan_with_unlocked_steps, objective="throughput")
    
    assert optimized["version"] == 2
    assert optimized["parent_version"] == 1


def test_optimize_plan_preserves_locked_steps():
    """Test that optimization preserves locked steps."""
    plan = {
        "id": "plan_test_locked",
        "org_id": "org_test_001",
        "design_id": "design_test_001",
        "revision_id": "rev_test_001",
        "quote_id": "quote_test_001",
        "quote_version": 1,
        "plan_revision": "A",
        "locked": False,
        "version": 1,
        "state": "draft",
        "steps": [
            {
                "step_id": "step_locked",
                "type": "CLEAN",
                "title": "Clean",
                "sequence": 1,
                "required": True,
                "locked_sequence": True,
                "soe_decision_id": "DEC-001",
            },
            {
                "step_id": "step_unlocked",
                "type": "SMT",
                "title": "SMT",
                "sequence": 2,
                "required": True,
                "locked_sequence": False,
            },
        ],
        "tests": [],
        "evidence_intent": [],
        "created_at": "2026-01-18T00:00:00Z",
        "updated_at": "2026-01-18T00:00:00Z",
    }
    save_plan(plan)
    
    optimized = optimize_plan_steps(plan, objective="throughput")
    
    # Locked step should remain first
    locked_step = next(s for s in optimized["steps"] if s["step_id"] == "step_locked")
    assert locked_step["sequence"] == 1


def test_generate_optimization_summary(plan_with_unlocked_steps):
    """Test optimization summary generation."""
    optimized = optimize_plan_steps(plan_with_unlocked_steps, objective="throughput")
    
    summary = generate_optimization_summary(plan_with_unlocked_steps, optimized)
    
    assert "objective" in summary
    assert "changes" in summary
    assert "constraints_preserved" in summary
    assert summary["constraints_preserved"] is True
