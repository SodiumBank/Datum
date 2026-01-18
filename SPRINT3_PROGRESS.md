# Sprint 3 Progress - Editable & Governed Manufacturing Plans

## ✅ Foundation Complete (Backend Core)

### Core Infrastructure ✅
1. ✅ **Sprint 3 Jira CSV** - All tickets defined
2. ✅ **Edit Rules** - `SPRINT3_EDIT_RULES.md` defines editable vs immutable fields
3. ✅ **Schema Updates** - DatumPlan schema updated for versioning, state, edit metadata

### Plan Editor ✅
4. ✅ **plan_editor.py** - Controlled editing with SOE constraint preservation
   - `validate_plan_edit()` - Validates edits preserve SOE constraints
   - `apply_plan_edit()` - Creates new version with edits
   - `create_plan_diff()` - Generates diff between versions
   - Prevents removal of SOE-required steps/tests/evidence without override
   - Prevents reordering of locked sequences without override

### Approval Workflow ✅
5. ✅ **plan_approval.py** - State machine: draft → submitted → approved/rejected
   - `submit_plan_for_approval()` - Draft → Submitted
   - `approve_plan()` - Submitted → Approved (locks plan)
   - `reject_plan()` - Submitted → Draft
   - All state transitions create audit events

### Plan Optimization ✅
6. ✅ **plan_optimizer.py** - Step ordering optimization
   - `optimize_plan_steps()` - Optimizes for throughput/cost/resource
   - Preserves SOE constraints (locked steps/sequences)
   - Only reorders unlocked steps
   - `generate_optimization_summary()` - Human-readable diff

### Plan Exporter ✅
7. ✅ **plan_exporter.py** - Production-ready exports
   - `export_plan_to_csv()` - CSV export (approved plans only)
   - `export_plan_to_json()` - JSON export with optional execution outputs
   - `export_placement_csv()` - Machine-readable XYRS format
   - All exports validate plan is approved before export

### API Endpoints ✅
8. ✅ **plans.py router** - Complete Sprint 3 API surface
   - `PATCH /plans/{plan_id}` - Edit plan (creates new version)
   - `POST /plans/{plan_id}/submit` - Submit for approval
   - `POST /plans/{plan_id}/approve` - Approve plan
   - `POST /plans/{plan_id}/reject` - Reject plan
   - `POST /plans/{plan_id}/optimize` - Optimize step ordering
   - `GET /plans/{plan_id}/versions` - Get all versions
   - `GET /plans/{plan_id}/versions/{version}` - Get specific version
   - `GET /plans/{plan_id}/diff` - Get diff between versions
   - `GET /plans/{plan_id}/export/csv` - Export to CSV
   - `GET /plans/{plan_id}/export/json` - Export to JSON
   - `GET /plans/{plan_id}/export/placement-csv` - Export placement CSV

## 🔄 In Progress / Pending

### UI Components (Pending)
- [ ] Ops UI - Editable Plan View
  - [ ] Editable plan components with inline validation
  - [ ] Read-only SOE locks (visual and functional)
  - [ ] Version history selector
  
- [ ] Ops UI - Approval & Audit Views
  - [ ] Approval action buttons (approve/reject based on role)
  - [ ] Audit log timeline

### Tests & Validation (Pending)
- [ ] Edit regression tests
- [ ] Optimization regression tests
- [ ] Approval validation tests
- [ ] Export validation tests
- [ ] SOE determinism regression tests
- [ ] Red-team test updates (allow overrides with justification, prevent silent overrides)

## Key Features Implemented

### ✅ Controlled Editing
- Plans can be edited (creates new version)
- SOE-required steps/tests/evidence protected
- Overrides require explicit reason and create audit trail
- Locked sequences cannot be reordered without override

### ✅ Approval Workflow
- Plans start in `draft` state
- Must be `submitted` before approval
- Only `approved` plans can be exported
- Approved plans are locked (immutable)
- Rejected plans return to `draft`

### ✅ Versioning & History
- Every edit creates new version
- Version history tracked
- Diffs between versions available
- Parent version references maintained

### ✅ Optimization
- Step ordering optimization for throughput/cost/resource
- Preserves SOE constraints (locked steps/sequences)
- Only optimizes unlocked steps
- Creates new version (does not mutate approved plans)

### ✅ Production Exports
- CSV export for plan steps and tests
- JSON export with full plan data and optional execution outputs
- Placement CSV in machine-readable XYRS format
- All exports validate plan is approved

## Next Steps

1. **UI Implementation** - Build editable plan view and approval UI
2. **Tests** - Add comprehensive test coverage for all Sprint 3 features
3. **Red-team Updates** - Update checks to allow overrides with justification
4. **Documentation** - Update API docs and user guides

## Status: 🟡 Backend Complete, UI & Tests Pending

Backend infrastructure is complete and ready for UI integration.
UI components and tests remain to be implemented.
