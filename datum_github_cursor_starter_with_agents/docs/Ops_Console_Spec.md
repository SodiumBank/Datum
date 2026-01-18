# Datum — Ops Console Spec (v1)

## Purpose
Provide a manufacturing control room to review, adjust parameters (not truths), approve, and lock Datum objects.

## Primary Views
1) Ops Queue
- Project, Tier, Risk, SLA, Status

2) Datum Quote Review
- Cost breakdown, assumptions, risk factors
- Approve (creates/advances lock state)

3) Datum Plan Review (Tier 2+)
- Step list with: trigger rule, parameters, acceptance, cost impact
- Locked sequence indicators (NASA polymerics)

4) Datum Tests
- Declared tests with parameters and acceptance criteria
- Customer approval required flags (e.g., TVAC)

5) Datum Outputs (Tier 3)
- Stencil / placement / selective solder / programming outputs
- Preview-only until approved + locked

6) Audit & Traceability
- Every change, who/when/why
- Exports for audits

## Forbidden Actions (System Enforced)
- Reorder locked sequences
- Delete mandatory steps
- Release outputs without approval
- Edit without justification and audit logging
