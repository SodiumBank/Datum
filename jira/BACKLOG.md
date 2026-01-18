# Datum — Backlog (Jira-ready)

## Initialize repo structure + CI
**Type:** Story  
**Epic:** Foundation & Repo  
**Priority:** High  
**Points:** 5

- Create monorepo layout per /docs
- Add linting, formatting, pre-commit
- Add Docker dev env skeleton
- Add schema validation CI step (ajv or python jsonschema)

**Acceptance:** CI passes on PR; schemas validate; basic project README exists.

---

## Implement Auth + RBAC (placeholder)
**Type:** Story  
**Epic:** Foundation & Repo  
**Priority:** High  
**Points:** 5

- Implement JWT auth skeleton in API
- Roles: CUSTOMER, OPS, QA, ADMIN
- Enforce role checks at route level

**Acceptance:** protected route requires token; role-based denial is logged.

---

## Gerber ZIP upload + storage API
**Type:** Story  
**Epic:** Gerber/BOM Ingestion  
**Priority:** High  
**Points:** 5

- POST /uploads/gerbers
- Store file + sha256
- Persist metadata per Datum Design Package schema

**Acceptance:** upload returns upload_id and sha256; stored files retrievable in dev.

---

## BOM upload + normalize
**Type:** Story  
**Epic:** Gerber/BOM Ingestion  
**Priority:** High  
**Points:** 5

- POST /uploads/bom
- Parse CSV/XLSX
- Normalize refdes/qty/mpn columns

**Acceptance:** normalized BOM items stored and validated against schema.

---

## Board metrics extraction (v1)
**Type:** Story  
**Epic:** Datum Quote Engine  
**Priority:** High  
**Points:** 5

- Parse gerbers to compute board outline size
- Count layers by file heuristics

**Acceptance:** metrics stored; surfaced in quote inputs.

---

## Pricing model v1 + deterministic Datum Quote
**Type:** Story  
**Epic:** Datum Quote Engine  
**Priority:** High  
**Points:** 8

- Implement cost stack placeholders: PCB_FAB, ASSEMBLY_LABOR, COMPONENTS, NRE, MARGIN
- Deterministic quote_version increments

**Acceptance:** same inputs -> identical quote; quote validates against schema.

---

## Supply chain risk flags (v1)
**Type:** Story  
**Epic:** Datum Quote Engine  
**Priority:** Medium  
**Points:** 5

- Add lead time lookup placeholders per part
- Flag long lead > 26 weeks
- Add SUPPLY_CHAIN_RISK line item

**Acceptance:** long-lead BOM triggers risk_factors and cost line.

---

## Customer UI: Upload flow
**Type:** Story  
**Epic:** Customer Web UI  
**Priority:** High  
**Points:** 5

- Next.js page: create project -> upload gerbers + BOM
- Show upload status and sha256

**Acceptance:** user can upload both files end-to-end.

---

## Customer UI: Quote view w/ breakdown
**Type:** Story  
**Epic:** Customer Web UI  
**Priority:** High  
**Points:** 5

- Render quote total + line items
- Render risk flags
- Show assumptions

**Acceptance:** quote renders from API response.

---

## Ops Console: Queue + Quote Review
**Type:** Story  
**Epic:** Ops Console  
**Priority:** High  
**Points:** 8

- Ops dashboard lists quotes needing review
- Approve quote (locks quote)

**Acceptance:** ops can lock quote; audit event recorded.

---

## Basic DRC checks (v1)
**Type:** Story  
**Epic:** Basic DRC  
**Priority:** Medium  
**Points:** 8

- Drill-to-copper clearance heuristic
- Copper-to-edge heuristic
- Flag as risk_factors

**Acceptance:** DRC produces deterministic findings and shows in quote.

---

## Rules engine skeleton (deterministic)
**Type:** Story  
**Epic:** DFM & Rules  
**Priority:** High  
**Points:** 8

- Load DatumRule JSON
- Evaluate triggers against extracted features
- Produce rule trace list

**Acceptance:** ruleset versioning supported; trace records rule_id + justification.

---

## Datum Plan generator v1
**Type:** Story  
**Epic:** Datum Plan Generator  
**Priority:** High  
**Points:** 8

- Generate steps from rules + quote
- Support locked_sequence steps
- Persist DatumPlan

**Acceptance:** plan validates against schema; steps include source_rules.

---

## NASA polymerics sequencing rules
**Type:** Story  
**Epic:** Datum Plan Generator  
**Priority:** High  
**Points:** 5

- If staking/coating/polymer present -> add CLEAN→BAKE→POLYMER→CURE→INSPECT
- Lock sequence true

**Acceptance:** cannot reorder locked steps; override requires audit reason.

---

## Datum Tests declarations v1
**Type:** Story  
**Epic:** Datum Tests  
**Priority:** High  
**Points:** 8

- Generate declared tests: XRAY for QFN/BGA, AOI for high-rel
- Support environmental test declarations: TVAC, VIBE, SHOCK, BURN_IN

**Acceptance:** tests validate against schema and link to plan revision.

---

## Datum Revision + Lock + Audit framework
**Type:** Story  
**Epic:** Audit/Locks/Revisions  
**Priority:** High  
**Points:** 8

- Implement DatumRevision creation
- Implement DatumLock endpoints
- Emit DatumAuditEvent on create/update/lock/override

**Acceptance:** audit entries generated for key actions; immutable revisions enforced after lock.

---

## AI agent test harness (launch + validate)
**Type:** Story  
**Epic:** AI Agents CI/Test Harness  
**Priority:** Medium  
**Points:** 8

- Add contract tests to validate schemas on generated objects
- Create agent-driven end-to-end test: upload->quote->lock
- Run in CI

**Acceptance:** automated test run produces artifacts; failures block merge.
