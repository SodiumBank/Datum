# Datum — Schema Map

This maps Datum JSON Schemas to the current API surface and the intended data flow.
It is a reference for wiring endpoints and validating responses.

## Entity Flow (High Level)
Org -> Project -> DesignPackage -> Quote -> Plan -> Tests/Outputs
Revision + Lock + Audit apply across Quote/Plan/Outputs.

## Schema Index
- `schemas/datum_org.schema.json` — Organization record with tiers and compliance modes.
- `schemas/datum_project.schema.json` — Project container under an org.
- `schemas/datum_design_package.schema.json` — Gerber + BOM + assumptions bundle.
- `schemas/datum_quote.schema.json` — Deterministic quote with risk factors and assumptions.
- `schemas/datum_plan.schema.json` — Deterministic plan derived from ruleset + quote.
- `schemas/datum_plan_step.schema.json` — Step entries used inside DatumPlan.
- `schemas/datum_tests.schema.json` — Declared verification intent linked to plan revision.
- `schemas/datum_outputs.schema.json` — Tier 3 execution artifacts linked to plan revision.
- `schemas/datum_revision.schema.json` — Immutable revision marker for quote/plan/outputs.
- `schemas/datum_lock.schema.json` — Lock record for immutable entities.
- `schemas/datum_audit_event.schema.json` — Audit log record for all critical actions.
- `schemas/datum_rule.schema.json` — Deterministic rule definition.
- `schemas/datum_rule_ref.schema.json` — Rule references inside plans/tests/outputs.

## Current API Mapping
These endpoints exist today but are placeholders and do not yet persist data.

| Endpoint | Response (Target Schema) | Status |
| --- | --- | --- |
| `POST /auth/login` | N/A (JWT token) | Implemented placeholder |
| `POST /uploads/gerbers` | Part of `DatumDesignPackage.gerber_set` | Placeholder response only |
| `POST /uploads/bom` | Part of `DatumDesignPackage.bom` | Placeholder response only |
| `POST /quotes/estimate` | `DatumQuote` | Placeholder response only |
| `GET /health` | N/A | Implemented |

## Planned API Mapping (Not Implemented)
Suggested endpoints and their primary schemas.

| Endpoint | Schema |
| --- | --- |
| `POST /orgs` | `DatumOrg` |
| `POST /projects` | `DatumProject` |
| `POST /design-packages` | `DatumDesignPackage` |
| `POST /quotes` | `DatumQuote` |
| `POST /plans` | `DatumPlan` |
| `POST /tests` | `DatumTests` |
| `POST /outputs` | `DatumOutputs` |
| `POST /revisions` | `DatumRevision` |
| `POST /locks` | `DatumLock` |
| `POST /audit-events` | `DatumAuditEvent` |
| `POST /rules` | `DatumRule` |

## Validation Notes
- `DatumQuote` must match the enum line item codes and include `inputs_fingerprint`.
- `DatumDesignPackage` requires both gerber and bom payloads with `sha256`.
- `DatumPlan` and `DatumTests` reference plan/quote revisions; locking should enforce immutability.
- `DatumOutputs` is Tier 3 only and must stay approval-gated.
