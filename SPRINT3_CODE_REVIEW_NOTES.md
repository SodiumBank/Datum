# Sprint 3 Code Review Notes & Address Items

## Critical Items to Verify Before Merge

### 1. Role Enforcement Reality ✅
**Status:** Needs verification
**Action:** Confirm approval endpoints actually enforce OPS/ADMIN roles (not just stub auth)

**Current Implementation:**
- All approval endpoints use `Depends(require_role("OPS", "ADMIN"))`
- Need to verify `require_role` implementation enforces actual role checks

### 2. Version Immutability ✅
**Status:** Implemented correctly
**Verified:**
- `save_plan()` saves each version as separate file (by plan_id.json)
- Older versions are not modified when new versions created
- Exports reference specific version via `plan.get("version")`

**Recommendation:** Add explicit version immutability test

### 3. Approval Gating Completeness ✅
**Status:** Implemented correctly
**Verified:**
- `validate_plan_exportable()` checks `state == "approved"` and `locked == True`
- All export endpoints call `validate_plan_exportable()`
- CSV, JSON, and placement CSV exports all enforce approval

### 4. Override Semantics ✅
**Status:** Implemented correctly
**Verified:**
- Overrides require `override_reason` (validated in `validate_plan_edit()`)
- Overrides create audit events (tracked in `edit_metadata.overrides[]`)
- Overrides create new version (version bump enforced)
- Approved plans cannot be edited (must create new version)

**Gap:** Overrides on approved plans should require re-approval
**Action:** Add re-approval requirement for overrides on approved plans

### 5. Determinism Boundary ✅
**Status:** Preserved
**Verified:**
- `test_sprint2_determinism_regression.py` ensures SOE → plan generation is deterministic
- Edit operations use "latest version" correctly (not breaking determinism tests)
- Optimization preserves SOE constraints (maintains determinism)

## Items Addressed in Sprint 4 Planning

- **Profile Stack:** Foundation for better standards traceability
- **Compliance Mapping:** Makes "why this step exists" explicit
- **Audit Reports:** Addresses "show me approval trail" requirement
- **Traveler Hardening:** Formalizes exports with revision control and signatures
