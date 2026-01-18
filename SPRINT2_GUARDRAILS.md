# Sprint 2 Design Guardrails (NON-NEGOTIABLE)

## Core Principle

**DatumPlan is declarative intent only - NO edits, NO overrides, NO approvals**

## What DatumPlan IS

✅ Ordered manufacturing steps  
✅ Derived from SOE + core analysis  
✅ Immutable once generated  
✅ Traceable back to SOE decisions  
✅ Reviewable by ops  

## What DatumPlan is NOT

❌ Editable by ops  
❌ Optimized by ops  
❌ A traveler  
❌ A machine program  
❌ Production-ready (that's Sprint 3+)  

## Enforcement Rules

1. **No UI Edits:** Ops UI can only VIEW DatumPlan, never edit it
2. **No Overrides:** No override flags or approval gates in Sprint 2
3. **No Approvals:** Approval workflow is Sprint 3+
4. **No Optimization:** No logic to "improve" the plan - it's deterministic
5. **No Production Exports:** No machine file generation or traveler export

## Agent Instructions

If agents ask:
- "Should ops be able to change this?" → **Answer: "No. That's Sprint 3."**
- "Should we add edit buttons?" → **Answer: "No. Read-only viewer only."**
- "Should ops approve the plan?" → **Answer: "No. That's Sprint 3."**
- "Should we optimize the sequence?" → **Answer: "No. Deterministic output only."**

## Sprint 2 Goal

Translate SOE decisions into a deterministic, reviewable manufacturing intent layer without allowing edits or overrides.

At end of Sprint 2:
- ✅ Ops can see exactly what manufacturing will require
- ✅ Ops can see tests, evidence, and process sequencing
- ✅ Ops can explain why each thing exists
- ❌ Ops CANNOT change anything (that's Sprint 3)
