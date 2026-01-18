"""Tests for DatumPlan editing (Sprint 3)."""

import pytest
from services.api.core.plan_editor import (
    validate_plan_edit,
    apply_plan_edit,
    create_plan_diff,
    _is_soe_locked_step,
    _is_soe_locked_test,
    _is_soe_locked_evidence,
)
from services.api.core.storage import save_plan, get_plan


@pytest.fixture
def sample_plan():
    """Create a sample plan for testing."""
    return {
        "id": "plan_test_001",
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
                "step_id": "step_soe_001",
                "type": "CLEAN",
                "title": "Clean",
                "sequence": 3,
                "required": True,
                "locked_sequence": True,
                "soe_decision_id": "DEC-12345678",
                "soe_why": {
                    "rule_id": "NASA.PROCESS.POLYMERICS.SEQUENCE",
                    "pack_id": "NASA_POLYMERICS",
                    "citations": ["NASA-STD-8739.1"],
                },
            },
        ],
        "tests": [
            {
                "test_id": "test_soe_001",
                "test_type": "TVAC",
                "title": "TVAC Test",
                "required": True,
                "soe_decision_id": "DEC-87654321",
            },
        ],
        "evidence_intent": [],
        "created_at": "2026-01-18T00:00:00Z",
        "updated_at": "2026-01-18T00:00:00Z",
    }


def test_is_soe_locked_step():
    """Test SOE lock detection for steps."""
    step_locked = {
        "step_id": "step_001",
        "soe_decision_id": "DEC-12345678",
    }
    step_unlocked = {
        "step_id": "step_002",
    }
    
    assert _is_soe_locked_step(step_locked) is True
    assert _is_soe_locked_step(step_unlocked) is False


def test_is_soe_locked_test():
    """Test SOE lock detection for tests."""
    test_locked = {
        "test_id": "test_001",
        "soe_decision_id": "DEC-12345678",
    }
    test_unlocked = {
        "test_id": "test_002",
    }
    
    assert _is_soe_locked_test(test_locked) is True
    assert _is_soe_locked_test(test_unlocked) is False


def test_validate_plan_edit_allows_non_soe_changes(sample_plan):
    """Test that non-SOE steps can be edited."""
    edited_plan = sample_plan.copy()
    edited_plan["steps"] = [
        s for s in edited_plan["steps"] if s["step_id"] != "step_002"
    ]
    
    is_valid, error_msg = validate_plan_edit(sample_plan, edited_plan)
    assert is_valid is True


def test_validate_plan_edit_blocks_soe_step_removal(sample_plan):
    """Test that SOE-required steps cannot be removed without override."""
    edited_plan = sample_plan.copy()
    edited_plan["steps"] = [
        s for s in edited_plan["steps"] if s["step_id"] != "step_soe_001"
    ]
    
    is_valid, error_msg = validate_plan_edit(sample_plan, edited_plan)
    assert is_valid is False
    assert "SOE-required step" in error_msg


def test_validate_plan_edit_allows_override_with_reason(sample_plan):
    """Test that SOE steps can be removed with override reason."""
    edited_plan = sample_plan.copy()
    edited_plan["steps"] = [
        s for s in edited_plan["steps"] if s["step_id"] != "step_soe_001"
    ]
    
    is_valid, error_msg = validate_plan_edit(
        sample_plan, edited_plan, allow_overrides=True, override_reason="Customer request"
    )
    assert is_valid is True


def test_validate_plan_edit_blocks_override_without_reason(sample_plan):
    """Test that override requires reason."""
    edited_plan = sample_plan.copy()
    edited_plan["steps"] = [
        s for s in edited_plan["steps"] if s["step_id"] != "step_soe_001"
    ]
    
    is_valid, error_msg = validate_plan_edit(
        sample_plan, edited_plan, allow_overrides=True, override_reason=None
    )
    assert is_valid is False
    assert "Override reason required" in error_msg


def test_validate_plan_edit_blocks_approved_plan_edit(sample_plan):
    """Test that approved plans cannot be edited."""
    sample_plan["state"] = "approved"
    sample_plan["locked"] = True
    
    edited_plan = sample_plan.copy()
    edited_plan["steps"] = sample_plan["steps"][:1]
    
    is_valid, error_msg = validate_plan_edit(sample_plan, edited_plan)
    assert is_valid is False
    assert "Approved plans are immutable" in error_msg


def test_apply_plan_edit_creates_new_version(sample_plan):
    """Test that editing creates a new version."""
    save_plan(sample_plan)
    
    edits = {
        "steps": sample_plan["steps"][:2],  # Remove one non-SOE step
    }
    
    edited_plan = apply_plan_edit(
        plan=sample_plan,
        edits=edits,
        user_id="user_test_001",
        edit_reason="Test edit",
        allow_overrides=False,
        override_reason=None,
    )
    
    assert edited_plan["version"] == 2
    assert edited_plan["parent_version"] == 1
    assert edited_plan["edit_metadata"]["edited_by"] == "user_test_001"
    assert edited_plan["edit_metadata"]["edit_reason"] == "Test edit"


def test_apply_plan_edit_tracks_overrides(sample_plan):
    """Test that overrides are tracked in edit metadata."""
    save_plan(sample_plan)
    
    edits = {
        "steps": [
            s for s in sample_plan["steps"] if s["step_id"] != "step_soe_001"
        ],
    }
    
    edited_plan = apply_plan_edit(
        plan=sample_plan,
        edits=edits,
        user_id="user_test_001",
        edit_reason="Test edit with override",
        allow_overrides=True,
        override_reason="Customer requested removal",
    )
    
    assert len(edited_plan["edit_metadata"]["overrides"]) > 0
    assert edited_plan["edit_metadata"]["overrides"][0]["reason"] == "Customer requested removal"


def test_create_plan_diff(sample_plan):
    """Test plan diff generation."""
    edited_plan = sample_plan.copy()
    edited_plan["version"] = 2
    edited_plan["steps"] = sample_plan["steps"][:2]  # Remove one step
    
    diff = create_plan_diff(sample_plan, edited_plan)
    
    assert "removed" in diff
    assert "steps" in diff["removed"]
    assert len(diff["removed"]["steps"]) == 1


def test_validate_plan_edit_blocks_locked_sequence_reorder(sample_plan):
    """Test that locked sequences cannot be reordered without override."""
    # Create plan with locked sequence
    plan_with_locked = sample_plan.copy()
    plan_with_locked["steps"] = [
        {
            "step_id": "step_clean",
            "type": "CLEAN",
            "sequence": 1,
            "locked_sequence": True,
            "soe_decision_id": "DEC-001",
        },
        {
            "step_id": "step_bake",
            "type": "BAKE",
            "sequence": 2,
            "locked_sequence": True,
            "soe_decision_id": "DEC-001",
        },
    ]
    
    # Try to reorder
    edited_plan = plan_with_locked.copy()
    edited_plan["steps"] = [
        {
            "step_id": "step_bake",
            "type": "BAKE",
            "sequence": 1,  # Reordered
            "locked_sequence": True,
            "soe_decision_id": "DEC-001",
        },
        {
            "step_id": "step_clean",
            "type": "CLEAN",
            "sequence": 2,  # Reordered
            "locked_sequence": True,
            "soe_decision_id": "DEC-001",
        },
    ]
    
    is_valid, error_msg = validate_plan_edit(plan_with_locked, edited_plan)
    assert is_valid is False
    assert "locked sequence" in error_msg.lower()
