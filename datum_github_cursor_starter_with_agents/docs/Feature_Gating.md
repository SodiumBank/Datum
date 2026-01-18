# Datum — Feature Gating Matrix & MVP Cutline

## Canonical Tiers
- **Tier 1: Datum Core** (quoting & transparency)
- **Tier 2: Datum Intelligence** (DFM + deterministic plan + tests + traceability)
- **Tier 3: Datum Authority** (execution outputs)

## MVP Cutline (Ship First)
### MUST SHIP (Tier 1)
- Gerber + BOM upload + normalization
- Deterministic quote
- Transparent cost breakdown
- Supply-chain risk flags + lead time tradeoffs
- Basic DRC
- High-level process outline
- Quote versioning
- Ops review of quotes

### MUST NOT SHIP (MVP)
- Machine programs / machine-specific exports
- Stencil aperture generation files
- Selective solder location authority
- Environmental test execution control
- Firmware programming outputs (Tier 3)
- Automatic blocking of builds

## Tier Enforcement Guardrails
- Tier evaluation is **server-side**
- Feature flags enforced at API layer
- Any override requires reason + audit log
- Lock boundaries create immutable revisions
