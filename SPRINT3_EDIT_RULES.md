# Sprint 3 Edit Rules (Editable vs Immutable)

## Core Principle

**SOE-derived fields are immutable. User-provided fields are editable.**

## Immutable Fields (SOE-Derived)

These fields come from SOE decisions and CANNOT be edited:
- `soe_run_id` - Reference to SOERun
- `soe_decision_ids[]` - List of SOE decision IDs
- Steps with `soe_decision_id` - Cannot be removed, reordered, or modified
- Steps with `locked_sequence: true` - Cannot be reordered
- `tests[]` entries with `soe_decision_id` - Cannot be removed
- `evidence_intent[]` entries with `soe_decision_id` - Cannot be removed
- `derived_from_ruleset` - Ruleset metadata is immutable

## Editable Fields (User-Provided)

These fields can be edited by Ops:
- `steps[]` without `soe_decision_id` - Can be reordered (if not locked)
- Step `sequence` - Can be changed (if step is not locked)
- Step `parameters` - Can be modified (for non-SOE steps)
- Step `acceptance.criteria` - Can be updated (for non-SOE steps)
- `notes` - Can be edited
- `eee_requirements` - Can be updated (not SOE-derived)

## Editable with Override (Requires Justification)

These SOE-derived fields can be overridden with explicit justification:
- Removing a step with `soe_decision_id` - Requires override with reason
- Reordering locked sequences - Requires override with reason
- Removing a required test - Requires override with reason
- Removing required evidence - Requires override with reason

## Edit Validation Rules

1. **Cannot remove SOE-required steps** without override
2. **Cannot reorder locked sequences** without override
3. **Cannot remove SOE-required tests** without override
4. **Cannot remove SOE-required evidence** without override
5. **Test dependencies must be preserved** - If test B depends on test A, A must come before B
6. **Step dependencies must be preserved** - If step B depends on step A, A must come before B
7. **All edits must include reason** - For audit trail

## Override Requirements

When overriding SOE constraints:
1. **User must provide explicit reason** (required)
2. **Override is logged in audit trail** (who, when, why)
3. **Override is visible in UI** (visual indicator)
4. **Override is stored in plan metadata** (for traceability)

## Versioning Rules

- Every edit creates a new plan version
- Original plan version is immutable
- Version history is maintained
- Diffs between versions are available

## Approval Rules

- Plans start in `draft` state
- Plans must be `submitted` before approval
- Only `approved` plans can be exported
- Rejected plans return to `draft` state
- Approval creates immutable snapshot
