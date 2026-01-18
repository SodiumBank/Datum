"""Tests for DatumPlan exports (Sprint 3)."""

import pytest
from services.api.core.plan_exporter import (
    validate_plan_exportable,
    export_plan_to_csv,
    export_plan_to_json,
)
from services.api.core.storage import save_plan


@pytest.fixture
def approved_plan():
    """Create an approved plan for export testing."""
    return {
        "id": "plan_test_export",
        "org_id": "org_test_001",
        "design_id": "design_test_001",
        "revision_id": "rev_test_001",
        "quote_id": "quote_test_001",
        "quote_version": 1,
        "plan_revision": "A",
        "locked": True,
        "lock_id": "lock_test_001",
        "version": 1,
        "state": "approved",
        "steps": [
            {
                "step_id": "step_001",
                "type": "FAB",
                "title": "PCB Fabrication",
                "sequence": 1,
                "required": True,
            },
        ],
        "tests": [
            {
                "test_id": "test_001",
                "test_type": "FUNCTIONAL",
                "title": "Functional Test",
                "required": True,
            },
        ],
        "evidence_intent": [],
        "created_at": "2026-01-18T00:00:00Z",
        "updated_at": "2026-01-18T00:00:00Z",
    }


def test_validate_plan_exportable_approved(approved_plan):
    """Test that approved plans are exportable."""
    is_exportable, error_msg = validate_plan_exportable(approved_plan)
    assert is_exportable is True


def test_validate_plan_exportable_draft():
    """Test that draft plans are not exportable."""
    plan = {
        "id": "plan_draft",
        "state": "draft",
        "locked": False,
    }
    
    is_exportable, error_msg = validate_plan_exportable(plan)
    assert is_exportable is False
    assert "draft" in error_msg.lower()


def test_validate_plan_exportable_submitted():
    """Test that submitted plans are not exportable."""
    plan = {
        "id": "plan_submitted",
        "state": "submitted",
        "locked": False,
    }
    
    is_exportable, error_msg = validate_plan_exportable(plan)
    assert is_exportable is False
    assert "submitted" in error_msg.lower()


def test_validate_plan_exportable_unlocked():
    """Test that unlocked approved plans are not exportable."""
    plan = {
        "id": "plan_unlocked",
        "state": "approved",
        "locked": False,
    }
    
    is_exportable, error_msg = validate_plan_exportable(plan)
    assert is_exportable is False
    assert "locked" in error_msg.lower()


def test_export_plan_to_csv(approved_plan):
    """Test CSV export."""
    save_plan(approved_plan)
    
    csv_content = export_plan_to_csv(approved_plan)
    
    assert "Plan Export" in csv_content
    assert "Steps" in csv_content
    assert "Tests" in csv_content
    assert "PCB Fabrication" in csv_content
    assert "Functional Test" in csv_content


def test_export_plan_to_csv_rejects_draft():
    """Test that CSV export rejects draft plans."""
    plan = {
        "id": "plan_draft",
        "state": "draft",
        "locked": False,
        "steps": [],
        "tests": [],
    }
    
    with pytest.raises(ValueError, match="draft"):
        export_plan_to_csv(plan)


def test_export_plan_to_json(approved_plan):
    """Test JSON export."""
    save_plan(approved_plan)
    
    json_data = export_plan_to_json(approved_plan)
    
    assert json_data["plan_id"] == approved_plan["id"]
    assert json_data["state"] == "approved"
    assert "steps" in json_data
    assert "tests" in json_data
    assert "export_timestamp" in json_data


def test_export_plan_to_json_rejects_draft():
    """Test that JSON export rejects draft plans."""
    plan = {
        "id": "plan_draft",
        "state": "draft",
        "locked": False,
        "steps": [],
        "tests": [],
    }
    
    with pytest.raises(ValueError, match="draft"):
        export_plan_to_json(plan)
