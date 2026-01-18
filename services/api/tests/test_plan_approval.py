"""Tests for DatumPlan approval workflow (Sprint 3)."""

import pytest
from services.api.core.plan_approval import (
    can_submit_plan,
    can_approve_plan,
    can_reject_plan,
    submit_plan_for_approval,
    approve_plan,
    reject_plan,
)
from services.api.core.storage import save_plan, get_plan, save_audit_event


@pytest.fixture
def draft_plan():
    """Create a draft plan for testing."""
    plan = {
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
            },
        ],
        "tests": [],
        "evidence_intent": [],
        "created_at": "2026-01-18T00:00:00Z",
        "updated_at": "2026-01-18T00:00:00Z",
    }
    save_plan(plan)
    return plan


def test_can_submit_draft_plan(draft_plan):
    """Test that draft plans can be submitted."""
    can_submit, error_msg = can_submit_plan(draft_plan)
    assert can_submit is True


def test_cannot_submit_non_draft_plan(draft_plan):
    """Test that non-draft plans cannot be submitted."""
    draft_plan["state"] = "submitted"
    can_submit, error_msg = can_submit_plan(draft_plan)
    assert can_submit is False
    assert "submitted" in error_msg.lower()


def test_cannot_submit_plan_without_steps():
    """Test that plans without steps cannot be submitted."""
    plan = {
        "id": "plan_test_empty",
        "state": "draft",
        "steps": [],
    }
    can_submit, error_msg = can_submit_plan(plan)
    assert can_submit is False
    assert "step" in error_msg.lower()


def test_submit_plan_for_approval(draft_plan):
    """Test submitting a plan for approval."""
    plan = submit_plan_for_approval(
        plan_id=draft_plan["id"],
        user_id="user_test_001",
        reason="Ready for review",
    )
    
    assert plan["state"] == "submitted"
    assert plan["updated_at"] != draft_plan["updated_at"]


def test_can_approve_submitted_plan(draft_plan):
    """Test that submitted plans can be approved."""
    draft_plan["state"] = "submitted"
    save_plan(draft_plan)
    
    can_approve, error_msg = can_approve_plan(draft_plan)
    assert can_approve is True


def test_cannot_approve_non_submitted_plan(draft_plan):
    """Test that only submitted plans can be approved."""
    can_approve, error_msg = can_approve_plan(draft_plan)
    assert can_approve is False
    assert "submitted" in error_msg.lower()


def test_approve_plan(draft_plan):
    """Test approving a plan."""
    # First submit
    submitted_plan = submit_plan_for_approval(
        plan_id=draft_plan["id"],
        user_id="user_test_001",
    )
    
    # Then approve
    approved_plan = approve_plan(
        plan_id=draft_plan["id"],
        user_id="user_test_002",
        reason="Plan approved",
    )
    
    assert approved_plan["state"] == "approved"
    assert approved_plan["locked"] is True
    assert approved_plan.get("lock_id") is not None


def test_can_reject_submitted_plan(draft_plan):
    """Test that submitted plans can be rejected."""
    draft_plan["state"] = "submitted"
    save_plan(draft_plan)
    
    can_reject, error_msg = can_reject_plan(draft_plan)
    assert can_reject is True


def test_cannot_reject_non_submitted_plan(draft_plan):
    """Test that only submitted plans can be rejected."""
    can_reject, error_msg = can_reject_plan(draft_plan)
    assert can_reject is False
    assert "submitted" in error_msg.lower()


def test_reject_plan(draft_plan):
    """Test rejecting a plan."""
    # First submit
    submitted_plan = submit_plan_for_approval(
        plan_id=draft_plan["id"],
        user_id="user_test_001",
    )
    
    # Then reject
    rejected_plan = reject_plan(
        plan_id=draft_plan["id"],
        user_id="user_test_002",
        reason="Needs revision",
    )
    
    assert rejected_plan["state"] == "draft"  # Returns to draft


def test_reject_plan_requires_reason(draft_plan):
    """Test that rejection requires a reason."""
    draft_plan["state"] = "submitted"
    save_plan(draft_plan)
    
    with pytest.raises(ValueError, match="reason"):
        reject_plan(
            plan_id=draft_plan["id"],
            user_id="user_test_001",
            reason="",  # Empty reason
        )
