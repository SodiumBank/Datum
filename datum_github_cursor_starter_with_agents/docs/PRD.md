# Datum — Product Requirements Document (PRD)

## Product Name
**Datum**

## Product Description (Official)
Datum is a manufacturing decision system that establishes a single reference truth from quote through execution.

## Core Principle
Every decision in Datum is derived from a declared reference and is traceable to its source.

## Problem Statement
High-grade electronics manufacturing suffers from a disconnect between design intent, quoting, manufacturability, process planning, testing, and execution.
The result is quote rework, late surprises, schedule slips, margin erosion, audit findings, and customer distrust.

## Vision
Treat manufacturing like engineering, not e-commerce:
- Transparent, explainable quotes
- Deterministic manufacturing intent (process plan + tests)
- Standards-driven sequencing and traceability
- Scales from commercial to space-grade
- Preserves human authority with audit-ready governance

## Goals & Success Metrics
- Upload → quote in < 5 minutes (Tier 1)
- Re-quotes < 10% of orders
- Process plan approval without rework > 80%
- Zero sequencing audit findings
- Quote → plan → outputs linked and revision-controlled

## Non-Goals (Guardrails)
- No automatic release of machine programs without human approval
- Not a full MES / shop-floor controller (initial phases)
- Not a marketplace
- Not a black-box AI that hallucinates process

## Personas
- Design Engineer
- Procurement / Program Manager
- Manufacturing / Ops Engineer
- Quality / Compliance

## Tiered Scope
### Tier 1 — Datum Core (Commercial Quoting)
- Gerber + BOM upload
- Deterministic quote + transparent breakdown
- Supply-chain risk flags
- Basic DRC
- High-level process outline (non-executable)
- Quote versioning

### Tier 2 — Datum Intelligence (Manufacturing Intent)
- Full DFM (fab + assembly)
- Deterministic Datum Plan (revision-controlled)
- NASA polymerics sequencing (clean → bake → polymer → cure → inspect)
- Inspection gates
- Datum Tests (declared verification)
- EEE handling: long-lead, A/B lot testing, cert traceability

### Tier 3 — Datum Authority (Execution Outputs; contract-gated)
- Stencil recommendations + apertures
- Placement outputs (XYRS neutral)
- Selective solder locations
- Lead forming instructions
- Programming steps + verification
- Reflow profile recs, AOI templates
- Always Ops-approved and locked

## Global Definition of Done
A feature is done when:
- Meets requirement + acceptance criteria
- Server-side tier enforcement
- Audit behavior validated
- Revisioning and locking validated
- Ops flow demonstrated
