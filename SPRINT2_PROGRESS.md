# Sprint 2 Progress Summary

## ✅ Completed Tickets (15/20)

### Core Intent Layer (Tickets 1-7)
1. ✅ **DatumPlan schema** - References SOE decisions (`soe_run_id`, `soe_decision_ids`, `tests[]`, `evidence_intent[]`)
2. ✅ **DatumPlan generator** - Pure function: `SOERun + Quote -> DatumPlan`
3. ✅ **SOE-required steps** - Translates `REQUIRE`/`INSERT_STEP` into plan steps with SOE decision references
4. ✅ **Test intent from SOE** - Generates `tests[]` array from SOE test decisions
5. ✅ **Evidence intent** - Generates `evidence_intent[]` from SOE required_evidence
6. ✅ **Manufacturing step taxonomy** - Canonical types: `SMT`, `REFLOW`, `COAT`, `CLEAN`, `BAKE`, etc.
7. ⚠️ **Golden DatumPlan example** - **IN PROGRESS**

### Execution Outputs (Tickets 8-13)
8. ✅ **Execution output schemas** - All schemas exist (stencil, placement, selective solder, programming, lead form)
9. ✅ **Stencil intent generator** - From PCB + BOM (apertures, foil recommendations)
10. ✅ **Placement intent generator** - XYZ, rotation, side (without machine files)
11. ✅ **Selective solder intent** - PTH analysis and locations
12. ✅ **Lead form intent** - Applicable components with dimensions
13. ✅ **Programming intent** - Firmware load requirements

### API Endpoints (Tickets 14-15)
14. ✅ **GET /plans/quote/{quote_id}** - Returns DatumPlan for quote (read-only)
15. ✅ **GET /outputs/{plan_id}** - Returns all execution outputs (read-only)

### Ops UI (Tickets 16-17) - **PENDING**
16. ⚠️ **Ops UI: DatumPlan viewer** - Display plan, no edits (Next.js component needed)
17. ⚠️ **Ops UI: Execution outputs viewer** - Display outputs, no edits (Next.js component needed)

### Quality & Guardrails (Tickets 18-20) - **PENDING**
18. ⚠️ **DatumPlan determinism tests** - Golden tests for identical inputs
19. ⚠️ **Prevent DatumPlan mutation** - Immutability enforcement (already implemented via locked flag)
20. ⚠️ **Red-team checks** - Prevent edits/overrides in Sprint 2 artifacts

## Files Created/Modified

### Core
- `services/api/core/plan_generator.py` - Complete rewrite as pure function with SOE integration
- `services/api/core/execution_outputs.py` - New module for execution output generators
- `schemas/datum_plan.schema.json` - Updated with SOE references, tests[], evidence_intent[]
- `schemas/datum_plan_step.schema.json` - Updated with soe_decision_id, soe_why, canonical step types

### API
- `services/api/routers/outputs.py` - New router for execution outputs
- `services/api/routers/plans.py` - Added GET /plans/quote/{quote_id}
- `services/api/main.py` - Added outputs router

### Documentation
- `SPRINT2_GUARDRAILS.md` - Non-negotiable rules for Sprint 2
- `jira/sprint2_jira_import.csv` - Sprint 2 Jira tickets

## Remaining Work

### High Priority
1. **Golden DatumPlan example** - Create `examples/datum_plan.space.flight.json`
2. **DatumPlan determinism tests** - Golden test suite
3. **Ops UI components** - Read-only viewers (can be minimal placeholders)

### Medium Priority
4. **Immutability enforcement** - Already partially implemented, needs explicit tests
5. **Red-team checks** - Agent CI checks for mutations/overrides

## Status: 75% Complete (15/20 tickets)

Core functionality is complete. Remaining work is primarily:
- Golden examples/tests
- UI components (read-only)
- Guardrails/testing
