# Datum — Cursor Rules (Non-negotiable)

You are an engineering agent working in the Datum repository.

## Core Product Laws
1) **Determinism:** Same inputs MUST yield identical DatumQuote / findings.
2) **Revision immutability:** Locked entities are immutable. Any change requires a new DatumRevision.
3) **Auditability:** Any create/update/lock/override emits DatumAuditEvent with who/when/why.
4) **Tier enforcement:** Feature gating is enforced server-side (API). No UI-only gating.
5) **Explainability:** Rules must cite their rule_id + justification in outputs (source_rules).

## Repo Guardrails
- Do not change JSON Schemas without:
  - updating docs and
  - adding/adjusting validation tests.
- Any new endpoint MUST have:
  - unit tests
  - schema validation where applicable
  - auth/role enforcement
- Do not add “magic” AI logic that cannot be reproduced.

## Implementation Rules
- Prefer small, reviewable PRs aligned to one Jira ticket.
- No breaking changes without migration notes.
- Add logging for security-relevant actions (auth, locks, overrides).
- Keep functions short; write tests for edge cases.

## Definition of Done (for any ticket)
- Lint + tests pass locally
- CI green
- Feature meets acceptance criteria
- No tier leaks
- Audit behavior verified

## If unclear
Make the smallest safe assumption and document it in code comments and/or the ticket notes.
