# Datum — Cursor + Agent Workflow

## Goals
- Break work into small, verifiable tickets
- Allow agents to implement with guardrails
- Enforce schemas, tier gating, and audit logs via CI

## Suggested workflow
1. Create Jira issues from `jira/datum_jira_import.csv`
2. For each ticket:
   - Create a branch: `ticket/<JIRA-KEY>-short-desc`
   - Agent implements changes + tests
   - Run CI locally (or via PR)
3. Merge only if:
   - Schemas still validate
   - Unit + contract tests pass
   - No tier leaks

## Agent guardrails (copy/paste into Cursor rules)
- Never modify schemas without updating docs and tests
- Feature flags enforced server-side (API)
- Any override must emit DatumAuditEvent
- Locked entities are immutable (new DatumRevision required)

## Test strategy (minimum)
- Schema validation: validate API outputs against JSON schemas
- Determinism test: same inputs yield identical DatumQuote
- Lock test: editing locked entity is rejected with audit event
