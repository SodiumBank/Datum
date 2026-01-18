# Sprint 4 Code Review Fixes Applied

## All 4 Blockers Fixed ✅

### 1. Compliance Router Mounted ✅
**File:** `services/api/main.py`
**Fix:** Added `compliance` import and `app.include_router(compliance.router, prefix="/compliance", tags=["compliance"])`
**Status:** Fixed - `/compliance/*` endpoints now available

### 2. active_profiles Exposed in SOE API ✅
**File:** `services/api/routers/soe.py`
**Fix:**
- Added `active_profiles: List[str] | None = None` to `EvaluateSOERequest`
- Pass `active_profiles=request.active_profiles` through in `/evaluate`, `/export-manifest`, `/decision-log`
**Status:** Fixed - Sprint 4 profile stack can be used via API

### 3. Determinism Bug Fixed ✅
**File:** `services/api/core/soe_engine.py`
**Fix:** Changed all `active_packs = list(set(...))` to `active_packs = sorted(set(...))`
**Impact:**
- Pack order is now deterministic (sorted alphabetically)
- Same inputs produce same pack order
- Fixes potential non-determinism in evidence fallback logic
**Status:** Fixed - All active_packs assignments use sorted()

### 4. Profile Layer Tagging Fixed ✅
**File:** `services/api/core/soe_engine.py`, `services/api/core/compliance_trace.py`
**Fix:**
- Use `TYPE_LAYER = {"BASE": 0, "DOMAIN": 1, "CUSTOMER_OVERRIDE": 2}` mapping
- Derive layer from `profile_type` not `profile_stack.index()`
- Applied in: decision tagging, profile_stack metadata, compliance trace
**Impact:**
- Layers are semantic (0/1/2) not sequential (0/1/2/3...)
- Multiple DOMAIN profiles both get layer=1, not different layers
- Higher layer wins on pack collision (customer override beats domain)
**Status:** Fixed - All layer assignments use semantic TYPE_LAYER mapping

### 5. Bonus: services/__init__.py Created ✅
**File:** `services/__init__.py`
**Fix:** Created empty package marker
**Status:** Fixed - Tests can now import `services.*` in pytest/CI

## Verification

All fixes maintain:
- ✅ Backward compatibility (works without active_profiles)
- ✅ Determinism (sorted pack lists)
- ✅ Correct semantics (semantic layers)
- ✅ API completeness (all endpoints wired)

## Files Modified

- `services/api/main.py` - Added compliance router
- `services/api/routers/soe.py` - Added active_profiles support
- `services/api/core/soe_engine.py` - Fixed determinism and layer tagging
- `services/api/core/compliance_trace.py` - Fixed layer tagging
- `services/__init__.py` - Created (new file)

## Status: ✅ Ready for Use/Merge

All code review blockers addressed. Sprint 4 profile stack is now:
- Fully wired (compliance router mounted)
- API-exposed (active_profiles parameter)
- Deterministic (sorted pack lists)
- Semantically correct (semantic layers)
