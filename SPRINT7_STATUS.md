# Sprint 7 Status - Stabilize Core, Enforce Tiers, Align Docs

## ✅ Story 1: Make Tests Runnable from Repo Root (COMPLETE)

### Fixes Applied
- ✅ Created `services/api/conftest.py` that adds repo root to `sys.path`
- ✅ This ensures `pytest` can find `services` module when run from repo root
- ✅ CI already uses `PYTHONPATH=../..` - conftest.py provides additional safety

### Verification
- ✅ `conftest.py` imports correctly
- ✅ `services.api.main` importable from repo root

### Remaining Tasks
- ⚠️ Update TESTING.md with canonical approach documentation
- ⚠️ Add smoke import test (`test_import_main.py`)

---

## ✅ Story 2: Fix Plan Generator Schema Compliance (COMPLETE)

### Fixes Applied
- ✅ Added `_ensure_step_schema_compliant()` helper function
- ✅ Removes `None` values for `parameters` and `acceptance` (omits optional fields)
- ✅ Populates `source_rules` with `BASELINE_DEFAULT_STEP` for all default steps
- ✅ Applied to all step creation paths:
  - `_create_default_steps()` - All default steps now have source_rules
  - `_convert_rule_actions_to_steps()` - Fixed None values
  - `_convert_soe_decisions_to_steps()` - Fixed None values
- ✅ Schema compliance check runs before plan validation

### Remaining Tasks
- ⚠️ Add regression test: `test_plan_generate_schema_validation.py`

---

## ✅ Story 3: Mount Profiles Router (ALREADY DONE in Sprint 6)

### Status
- ✅ Profiles router already mounted in `main.py` (line 17)
- ✅ All `/profiles/*` endpoints accessible

### Remaining Tasks
- ⚠️ Add contract test for `/profiles` routes

---

## 🚧 Story 4: Implement Outputs Export Endpoint (IN PROGRESS)

### Current State
- ⚠️ `POST /outputs/{plan_id}/export` documented in `API_ENDPOINTS.md` but NOT implemented
- ✅ Plan exports exist: `/plans/{plan_id}/export/csv`, `/export/json`, `/export/placement-csv`

### Decision Needed
- Option A: Implement `POST /outputs/{plan_id}/export` with approval + tier gating
- Option B: Remove from `API_ENDPOINTS.md` (defer to future sprint)

---

## 🚧 Story 5: Align API_ENDPOINTS.md with Real Routers (PENDING)

### Issues Found
- ⚠️ `/outputs/{plan_id}/export` documented but not implemented
- Need to audit all routers vs docs

---

## 🚧 Story 6: Strengthen Server-Side Tier Enforcement (PENDING)

### Current State
- ⚠️ `plan_exporter.py` checks approval but NOT tier
- Need to add tier checks for Tier 3 exports

---

## ✅ Story 7: Repo Hygiene (COMPLETE)

### Fixes Applied
- ✅ Added `.pytest_cache/` and `**/.pytest_cache/` to `.gitignore`
- ✅ Cache directories not tracked (were already untracked)

---

## Files Modified (Sprint 7 So Far)

1. `services/api/conftest.py` - New file for pytest path resolution
2. `services/api/core/plan_generator.py` - Schema compliance fixes
3. `.gitignore` - Added .pytest_cache patterns

---

## Next Steps

1. Complete outputs export decision (implement or remove from docs)
2. Add tests (smoke import, plan schema regression, profiles contract)
3. Implement tier enforcement for exports
4. Audit and align API_ENDPOINTS.md
