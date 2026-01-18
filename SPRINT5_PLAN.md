# Sprint 5 Plan - Auditor-Grade Reporting & Profile Lifecycle

## Vision

**Sprint 5 transforms Datum from a planning tool into an auditor-grade system of record.**

After Sprint 5, Datum becomes:
> "The AS9100 / ISO 13485 / NASA compliance system of record"

This is a fundamental positioning shift—from "tool that helps plan" to "system that proves compliance."

---

## Sprint 5 Goals

### Primary Goal
**Lock Datum in as an auditor-grade system of record** with:
- Formal auditor-ready reports
- Governed standards profile lifecycle
- Cryptographic export integrity
- Complete audit trail immutability

### Secondary Goals
- Profile lifecycle management (draft → approved → deprecated)
- Profile versioning and history
- Program/customer profile bundles
- Export hardening for audits

---

## Key Features

### 1. Auditor-Grade Compliance Reports
**Why:** Auditors need formal, comprehensive reports they can cite in findings.

**What:**
- PDF and HTML report generation
- Standard sections: scope, standards coverage, deviations, overrides, approvals, traceability
- Clause coverage matrix (plan steps → standards clauses)
- Explicit override/deviations section with justifications

**Impact:** Datum reports become evidence-grade artifacts.

### 2. Standards Profile Lifecycle
**Why:** Standards profiles must be governed like plans—no ad-hoc modifications.

**What:**
- Profile states: `draft`, `submitted`, `approved`, `deprecated`
- Profile approval workflow (submit, approve, reject)
- Immutability for approved profiles (must create new version)
- Approval endpoints similar to plan approval

**Impact:** Profile governance matches plan governance.

### 3. Profile Versioning & History
**Why:** Auditors need to see how standards evolved over time.

**What:**
- Profile version identifiers and parent references
- Profile diff engine (compare versions)
- Profile history API (GET versions, GET diffs)

**Impact:** Complete lineage for standards decisions.

### 4. Profile Bundles
**Why:** Programs/customers often need combinations of profiles.

**What:**
- Bundle schema referencing multiple profiles
- SOE bundle selection (use bundle instead of individual profiles)
- Bundle traceability in compliance reports

**Impact:** Easier program-level compliance management.

### 5. Export Hardening
**Why:** Exported artifacts must survive external audits.

**What:**
- Cryptographic hash (SHA256) for all exports
- Provenance metadata (plan version, profile stack, approvals) embedded
- Read-only export enforcement (cannot regenerate after revocation)

**Impact:** Exports are tamper-evident and auditable.

### 6. Compliance Red-Team Expansion
**Why:** Prevent abuse of audit and profile lifecycle features.

**What:**
- Profile downgrade attack tests (block deprecated/draft in production)
- Approval bypass tests (block reports/exports without approvals)

**Impact:** Security guarantees for audit features.

---

## Architecture Considerations

### Report Generation
- **Format:** PDF (primary), HTML (secondary)
- **Template Engine:** Consider `reportlab` for PDF, Jinja2 for HTML
- **Data Source:** Approved plans + compliance traces + profile stacks

### Profile Lifecycle
- **States:** Mirror plan states (draft, submitted, approved, deprecated)
- **Storage:** Extend `standards_profiles/` with version directories or database
- **API:** Reuse plan approval patterns in new `profiles` router

### Versioning
- **Schema Extension:** Add `version`, `parent_profile_id`, `version_history` to profile schema
- **Storage:** Versioned JSON files or database with versioning support
- **Comparison:** JSON diff algorithm (similar to plan diff)

### Export Hardening
- **Hashing:** SHA256 for all exports
- **Metadata:** Embed as JSON/XML in export headers or separate manifest
- **Read-only:** Store export hash in audit log, verify on regeneration

---

## Success Criteria

### Must Have
1. ✅ Auditor-grade compliance reports (PDF + HTML)
2. ✅ Profile lifecycle states and approval workflow
3. ✅ Profile versioning with history API
4. ✅ Export hardening (hash + provenance)
5. ✅ Red-team tests for profile lifecycle abuse

### Nice to Have
1. Profile bundles (can defer if complex)
2. Ops UI for compliance views (backend-first)
3. Audit playbooks documentation (can be async)

---

## Dependencies on Sprint 4

Sprint 5 builds on:
- ✅ Profile stack architecture (Sprint 4)
- ✅ Compliance traceability (Sprint 4)
- ✅ Plan approval workflow (Sprint 3)

---

## Risk Mitigation

### High Risk: Report Generation Complexity
**Mitigation:** Start with HTML, add PDF if time permits. Use existing compliance trace data.

### Medium Risk: Profile Versioning Storage
**Mitigation:** Start with versioned JSON files, migrate to database later if needed.

### Low Risk: Export Hardening
**Mitigation:** SHA256 hashing is straightforward, metadata embedding is simple.

---

## Timeline Estimate

**Total:** ~40-50 story points

1. **Reports** (12 pts) - 2-3 days
2. **Profile Lifecycle** (8 pts) - 1-2 days
3. **Profile Versioning** (8 pts) - 1-2 days
4. **Profile Bundles** (5 pts) - 1 day
5. **Export Hardening** (5 pts) - 1 day
6. **Red-Team Tests** (5 pts) - 1 day
7. **UI Components** (5 pts) - 1 day (optional)
8. **Documentation** (3 pts) - 0.5 days (optional)

**Total:** ~10-12 working days

---

## Next Steps

1. ✅ Create Sprint 5 Jira CSV
2. Review and refine Sprint 5 plan
3. Start with auditor report structure definition
4. Implement profile lifecycle states
5. Build report generator

---

## Status: 📋 Ready to Start

**Sprint 5 Jira CSV created.** Ready to begin implementation when approved.
