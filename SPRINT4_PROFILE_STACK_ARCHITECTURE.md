# Sprint 4: Standards Profile Stack Architecture

## Overview

Sprint 4 introduces a **layered standards profile system** that enables multi-industry compliance with customer-specific deltas while maintaining traceability to source standards.

## Profile Hierarchy

```
┌─────────────────────────────────────────┐
│ BASE PROFILE (IPC/core manufacturing)  │
│  - IPC-A-610, IPC-J-STD-001 base       │
│  - Core manufacturing physics           │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ DOMAIN PROFILE (Industry-specific)      │
│  - AS9100 (aerospace)                   │
│  - ISO 13485 (medical)                  │
│  - IATF 16949 (automotive)              │
│  - NASA addenda (space)                 │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ CUSTOMER_OVERRIDE PROFILE (Program)     │
│  - Customer-specific contract rules     │
│  - Program-specific constraints         │
└─────────────────────────────────────────┘
```

## Profile Types

### 1. BASE Profile
- **Purpose:** Core manufacturing standards (IPC, J-STD)
- **Characteristics:**
  - No parent profiles
  - Universal across industries
  - Defines base manufacturing process

### 2. DOMAIN Profile
- **Purpose:** Industry-specific standards (AS9100, ISO 13485, etc.)
- **Characteristics:**
  - Inherits from BASE profile
  - Industry-specific (space, medical, automotive)
  - Adds domain requirements

### 3. CUSTOMER_OVERRIDE Profile
- **Purpose:** Program/contract-specific rules
- **Characteristics:**
  - Inherits from DOMAIN profile
  - Customer/contract-specific
  - Overrides or extends domain requirements

## Profile Inheritance Rules

### Override Modes

1. **STRICT:** No overrides allowed (use parent as-is)
2. **ADDITIVE:** Add requirements to parent (default)
3. **REPLACE:** Replace parent requirements entirely

### Conflict Resolution

1. **ERROR:** Fail if conflicts detected (default, safest)
2. **PARENT_WINS:** Parent profile takes precedence
3. **CHILD_WINS:** Child profile takes precedence

## Profile Selection in SOERun

```json
{
  "soe_version": "1.0.0",
  "industry_profile": "space",
  "active_profiles": [
    "BASE_IPC",
    "AS9100_DOMAIN",
    "NASA_POLYMERICS_DOMAIN",
    "CUSTOMER_PROGRAM_001_OVERRIDE"
  ],
  "profile_stack": [
    {"profile_id": "BASE_IPC", "profile_type": "BASE", "layer": 0},
    {"profile_id": "AS9100_DOMAIN", "profile_type": "DOMAIN", "layer": 1},
    {"profile_id": "NASA_POLYMERICS_DOMAIN", "profile_type": "DOMAIN", "layer": 1},
    {"profile_id": "CUSTOMER_PROGRAM_001_OVERRIDE", "profile_type": "CUSTOMER_OVERRIDE", "layer": 2}
  ],
  "decisions": [
    {
      "id": "DEC-12345678",
      "profile_source": "AS9100_DOMAIN",
      "clause_reference": "8.5.1",
      "rule_id": "AS9100.TEST.TVAC.REQUIRED",
      ...
    }
  ]
}
```

## Compliance Traceability

Every plan step/test/evidence must trace back to:
1. **Source Standard:** Which standard requires this?
2. **Clause Reference:** Which clause/section?
3. **Profile Layer:** Which profile in the stack?
4. **Decision ID:** Which SOE decision enforced it?

### Example Traceability

```json
{
  "step_id": "step_tvac_001",
  "type": "TEST",
  "title": "TVAC Test",
  "soe_decision_id": "DEC-12345678",
  "compliance_trace": {
    "source_standard": "AS9100",
    "clause": "8.5.1",
    "section": "Production and Service Provision - Control of Production",
    "profile_source": "AS9100_DOMAIN",
    "profile_layer": 1,
    "rule_id": "AS9100.TEST.TVAC.REQUIRED",
    "pack_id": "AS9100_BASE"
  }
}
```

## Profile Validation Rules

1. **No Circular Dependencies:** Profile A cannot inherit from Profile B if B inherits from A
2. **Type Constraints:** DOMAIN can only inherit from BASE, CUSTOMER_OVERRIDE can only inherit from DOMAIN
3. **Conflict Detection:** Same rule_id in parent and child must be resolved
4. **Standards Pack Compatibility:** Packs must be compatible with profile's industry domain

## Integration Points

### SOE Engine
- Loads profiles in stack order (BASE → DOMAIN → CUSTOMER_OVERRIDE)
- Resolves inheritance and conflicts
- Tags decisions with profile source and clause references

### Plan Generator
- Includes compliance trace in plan steps
- Links steps to profile layers and standards clauses
- Preserves traceability through edits and overrides

### Compliance Reporting
- Aggregates traceability across all plan steps
- Shows coverage by standard and clause
- Highlights overrides and deviations

## Files & Schemas

- `schemas/standards_profile.schema.json` - Profile schema
- `services/api/core/profile_stack.py` - Profile inheritance and resolution
- `services/api/core/compliance_trace.py` - Traceability mapping
- `standards_profiles/` - Profile JSON files
