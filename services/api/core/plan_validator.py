"""Plan validator - ensures locked sequences cannot be reordered without audit."""

from typing import Any, Dict, List


def validate_step_reorder(
    original_plan: Dict[str, Any],
    updated_steps: List[Dict[str, Any]],
    override_reason: str | None = None,
) -> tuple[bool, str]:
    """
    Validate that locked steps are not reordered.
    
    Args:
        original_plan: Original plan with steps
        updated_steps: Updated list of steps
        override_reason: Reason for override (required if locked steps are modified)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    original_steps = original_plan.get("steps", [])
    
    # Create maps of step_id to sequence for locked steps
    original_locked: Dict[str, int] = {}
    for step in original_steps:
        if step.get("locked_sequence"):
            step_id = step.get("step_id")
            sequence = step.get("sequence")
            if step_id:
                original_locked[step_id] = sequence
    
    if not original_locked:
        # No locked steps, allow reordering
        return True, ""
    
    # Check if any locked steps have changed sequence
    updated_locked: Dict[str, int] = {}
    for step in updated_steps:
        step_id = step.get("step_id")
        if step_id in original_locked:
            sequence = step.get("sequence")
            updated_locked[step_id] = sequence
    
    # Check for sequence changes
    reordered_steps = []
    for step_id, original_seq in original_locked.items():
        if step_id in updated_locked:
            new_seq = updated_locked[step_id]
            if new_seq != original_seq:
                reordered_steps.append(step_id)
    
    if reordered_steps:
        # Locked steps were reordered
        if not override_reason or not override_reason.strip():
            return False, (
                f"Locked steps cannot be reordered without an override reason. "
                f"Reordered step IDs: {', '.join(reordered_steps)}"
            )
        
        # Override allowed with reason (will need audit event)
        return True, "Override allowed with reason"
    
    return True, ""


def validate_locked_sequence_integrity(steps: List[Dict[str, Any]]) -> tuple[bool, str]:
    """
    Validate that locked sequences maintain their relative order.
    
    For NASA polymerics, the sequence must be: CLEAN → BAKE → POLYMER → CURE → INSPECT
    """
    # Find locked steps and their sequences
    locked_steps = [
        (step.get("type"), step.get("sequence"))
        for step in steps
        if step.get("locked_sequence")
    ]
    
    if not locked_steps:
        return True, ""
    
    # Sort by sequence
    locked_steps.sort(key=lambda x: x[1])
    
    # Check NASA polymerics sequence
    expected_order = ["CLEAN", "BAKE", "POLYMER", "CURE", "INSPECT"]
    found_types = [step_type for step_type, _ in locked_steps]
    
    # Check if all expected steps are present (if any are locked)
    has_polymerics = any(t in found_types for t in expected_order)
    if has_polymerics:
        # Verify order for steps that are present
        filtered_order = [t for t in expected_order if t in found_types]
        if found_types != filtered_order:
            return False, (
                f"Locked polymerics sequence violation. "
                f"Expected order: {' → '.join(filtered_order)}, "
                f"Found: {' → '.join(found_types)}"
            )
    
    return True, ""


def can_modify_locked_step(
    step_id: str,
    plan: Dict[str, Any],
    override_reason: str | None = None,
) -> tuple[bool, str]:
    """
    Check if a locked step can be modified.
    
    Args:
        step_id: ID of the step to modify
        plan: Plan containing the step
        override_reason: Reason for override (required if step is locked)
    
    Returns:
        Tuple of (can_modify, error_message)
    """
    steps = plan.get("steps", [])
    
    # Find the step
    step = None
    for s in steps:
        if s.get("step_id") == step_id:
            step = s
            break
    
    if not step:
        return False, f"Step not found: {step_id}"
    
    # Check if locked
    if step.get("locked_sequence"):
        if not override_reason or not override_reason.strip():
            return False, (
                f"Step {step_id} is locked and cannot be modified without an override reason. "
                f"Step: {step.get('type')} - {step.get('title')}"
            )
        
        # Override allowed with reason
        return True, "Override allowed with reason"
    
    return True, ""
