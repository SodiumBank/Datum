# Sprint 6 Status - Close Sprint 5 Gaps + Multi-Industry Expansion

## ✅ Sprint 5 Gap Fixes (Sprint 6 Story 1-3)

### 1. Profiles Router Mounting ✅
- **Status:** Router already mounted in `main.py` (line 17: `app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])`)
- **Verification:** Router is imported and included correctly
- **Action:** Verified working - no changes needed

### 2. PDF Generation Contract ✅
- **Status:** Fixed - PDF format now explicitly rejected with clear error message
- **Change:** `POST /compliance/plans/{plan_id}/reports/generate` now rejects `format=pdf` with 400 error
- **Message:** "Unsupported format: pdf. Currently only 'html' is supported. PDF generation is deferred to a future sprint."
- **Impact:** No more 500 errors - clear contract to clients

### 3. Bundle/Profile Merge Determinism ✅
- **Status:** Fixed - removed `set()` from profile merge
- **Change:** `soe_engine.py` now uses deterministic merge:
  - Preserves order from `active_profiles` then `bundle_profiles`
  - Removes duplicates while maintaining order (first occurrence wins)
  - Sorts final list by `profile_id` for consistent ordering
- **Impact:** Audit artifacts will have stable profile ordering

### 4. Profile Lifecycle Immutability Enforcement ✅
- **Status:** Enhanced - `_save_profile_with_state()` now checks immutability
- **Change:** Approved profiles cannot change state (except to deprecated)
- **Enforcement:** `ensure_profile_immutable()` called in `create_profile_version()` 
- **Impact:** Approved profiles protected from accidental modification

---

## 🚧 In Progress (Sprint 6 Stories 4-6)

### Story 4: Profile Lifecycle Enforcement in Write Paths
- **Status:** Partially complete
- ✅ `_save_profile_with_state()` enforces immutability
- ✅ `create_profile_version()` checks immutability before versioning
- ⚠️ Need audit of all profile write paths (if any others exist)

### Story 5: Multi-Industry Standards Layer Model
- **Status:** Not started
- ⚠️ Need to create domain profiles for aerospace/medical/automotive
- ⚠️ Update industry_profiles JSON files with default packs
- ⚠️ Add starter standards packs per industry

### Story 6: Audit Artifact Consistency Checks
- **Status:** Not started
- ⚠️ Need to implement audit integrity checker
- ⚠️ Add examples and documentation

---

## Files Modified (Sprint 6 Gap Fixes)

1. `services/api/routers/compliance.py` - PDF format rejection
2. `services/api/core/soe_engine.py` - Deterministic profile merge
3. `services/api/core/profile_lifecycle.py` - Immutability enforcement in `_save_profile_with_state()`
4. `services/api/core/profile_versioning.py` - Immutability check in `create_profile_version()`

---

## Status: Sprint 5 Gaps Closed ✅

**Critical Sprint 5 issues resolved:**
- ✅ Profiles router is mounted and accessible
- ✅ PDF format properly rejected (no 500s)
- ✅ Profile merge is deterministic
- ✅ Profile immutability enforced

**Remaining Sprint 6 work:**
- Multi-industry domain profiles
- Audit artifact consistency checks
