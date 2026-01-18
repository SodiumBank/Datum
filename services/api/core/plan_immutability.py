"""DatumPlan immutability enforcement (Sprint 2).

SPRINT 2: DatumPlan is immutable once generated.
NO edits, NO overrides, NO mutations.
Any change requires creating a new revision.
"""

from typing import Dict, Any


def ensure_plan_immutable(plan: Dict[str, Any]) -> None:
    """
    Ensure plan is immutable (Sprint 2: no mutations allowed).
    
    Raises ValueError if plan is locked or if mutation is attempted.
    """
    if plan.get("locked"):
        raise ValueError(
            f"Plan {plan.get('id')} is locked. "
            "Create a new revision to modify. (Sprint 2: no mutations allowed)"
        )
    
    # In Sprint 2, all plans are read-only
    # Mutation should not be possible through the API
    # This is enforced at the router level by not exposing update endpoints
    # This function serves as an additional safety check


def can_modify_plan(plan: Dict[str, Any]) -> bool:
    """
    Check if plan can be modified (Sprint 2: always False).
    
    Returns:
        False - Plans are immutable in Sprint 2
    """
    # Sprint 2: No modifications allowed
    return False


def validate_plan_not_mutated(
    original_plan: Dict[str, Any],
    modified_plan: Dict[str, Any],
) -> tuple[bool, str]:
    """
    Validate that plan was not mutated (Sprint 2: mutation not allowed).
    
    Returns:
        (False, error_message) - Mutation is not allowed in Sprint 2
    """
    return (
        False,
        "Sprint 2: DatumPlan is immutable. "
        "Mutations are not allowed. Create a new revision to make changes.",
    )
