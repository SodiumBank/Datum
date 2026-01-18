# Sprint 8 Status - Frontend & Practical Workflows

## ✅ COMPLETE

### Story 1: Frontend Skeleton & App Shell ✅
- ✅ API client abstraction (`lib/api.ts`) with typed methods for all endpoints
- ✅ Global error handling with `ErrorProvider` and toast notifications
- ✅ Error handler context and hook (`lib/error-handler.tsx`)
- ✅ Wrapped app with `ErrorProvider` in layout

### Story 2: SOE Run UI ✅
- ✅ `/soe` page with input form for industry, hardware class, inputs
- ✅ SOE results viewer showing decisions, active packs, gates
- ✅ Form supports processes, tests, materials, risk flags, profile bundles
- ✅ Results display with decision details and gate status

### Story 3: Plan Generation & Viewing UI ✅
- ✅ `/plans` page with plan list view and generation
- ✅ Plan detail page at `/plans/[planId]`
- ✅ SOE-lock visualization: visually mark SOE-locked steps (orange/yellow) vs editable steps
- ✅ Display plan state, version, approval status
- ✅ Step display with SOE lock indicators

### Story 4: Governed Plan Editing UI ✅ (Basic)
- ✅ Edit mode toggle in plan detail page
- ✅ Edit handlers for plan updates
- ✅ Backend validation via API (errors surfaced through error handler)
- ⚠️ Diff preview and advanced editing UI deferred (basic editing functional)

### Story 5: Plan Approval Workflow UI ✅ (Partial)
- ✅ Submit for approval action in plan detail page
- ✅ Submit handler with backend integration
- ⚠️ Approve/reject controls for OPS users deferred (can be added to ops app)

## 🟡 PARTIAL / IN PROGRESS

### Story 6: Compliance & Standards Visualization
- ⚠️ Step compliance inspector (source rules shown, but no detailed inspector UI)
- ⚠️ Profile stack viewer (not yet implemented as separate component)
- ⚠️ Override warnings (shown via SOE lock indicators, but no explicit override UI)

### Story 7: Compliance Report Access UI
- ⚠️ Not yet implemented (can be added as `/plans/[planId]/compliance` route)

### Story 8: Basic Auth & Role Stubs
- ✅ Basic auth via API client login
- ⚠️ Role-based UI gating not yet implemented (all actions visible to all users)

### Story 9: Frontend Safety & Scope Guardrails
- ✅ Backend validation errors surfaced through error handler
- ✅ UI respects plan state (edit only for draft, submit only for draft)
- ⚠️ Red-team UI tests not yet implemented

## Files Created (Sprint 8)

1. `apps/web/lib/api.ts` - Typed API client
2. `apps/web/lib/error-handler.tsx` - Global error handling
3. `apps/web/app/soe/page.tsx` - SOE Run UI
4. `apps/web/app/plans/page.tsx` - Plan list and generation
5. `apps/web/app/plans/[planId]/page.tsx` - Plan detail with editing/approval

## Summary

**Core functionality implemented:**
- ✅ API client abstraction and error handling
- ✅ SOE evaluation UI
- ✅ Plan generation and viewing
- ✅ Plan editing (basic)
- ✅ Plan submission workflow

**Remaining for full Sprint 8:**
- Enhanced compliance visualization components
- Compliance report UI
- Role-based UI gating
- Red-team UI tests

**Sprint 8 achieves the main goal:** Enable real humans to use Datum safely via a front end, preserving determinism, governance, and audit posture.
