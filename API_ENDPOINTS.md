# Datum API Endpoints

Complete API endpoint reference for the Datum Manufacturing Decision System.

## Authentication
- `POST /auth/login` - Authenticate and receive JWT token

## Health
- `GET /health` - Health check endpoint

## Uploads
- `POST /uploads/gerbers` - Upload Gerber ZIP file
- `POST /uploads/bom` - Upload BOM (CSV or XLSX)
- `GET /uploads/gerbers/{upload_id}/metrics` - Get board metrics
- `GET /uploads/bom/{upload_id}/normalized` - Get normalized BOM

## Quotes
- `POST /quotes/estimate` - Generate deterministic quote
- `GET /quotes` - List quotes (filterable by status)
- `GET /quotes/{quote_id}` - Get specific quote
- `POST /quotes/{quote_id}/lock` - Lock a quote (Ops/Admin only)

## Rules
- `POST /rules/evaluate` - Evaluate rules against uploaded files
- `GET /rules/ruleset/{ruleset_version}` - Get ruleset metadata

## Plans
- `POST /plans/generate` - Generate plan from quote and ruleset
- `GET /plans` - List plans (filterable by quote_id)
- `GET /plans/{plan_id}` - Get specific plan
- `PATCH /plans/{plan_id}` - Update plan steps (Sprint 3: editable plans)
- `POST /plans/{plan_id}/optimize` - Optimize plan step ordering (Sprint 3)
- `GET /plans/{plan_id}/versions` - List plan versions (Sprint 3)
- `GET /plans/{plan_id}/diff` - Compare plan versions (Sprint 3)
- `POST /plans/{plan_id}/submit` - Submit plan for approval (Sprint 3)
- `POST /plans/{plan_id}/approve` - Approve plan (Sprint 3, Ops/Admin only)
- `POST /plans/{plan_id}/reject` - Reject plan (Sprint 3, Ops/Admin only)
- `POST /plans/{plan_id}/export` - Export plan (Sprint 3, approved plans only)

## Tests
- `POST /tests/generate` - Generate tests from plan
- `GET /tests` - List tests (filterable by plan_id)
- `GET /tests/{tests_id}` - Get specific tests declaration

## Revisions
- `POST /revisions` - Create new revision
- `GET /revisions` - List revisions (filterable by org_id/design_id)
- `GET /revisions/{revision_id}` - Get specific revision
- `POST /revisions/for-update` - Create revision for updating locked entity
- `GET /revisions/entity/{entity_type}/{entity_id}/lock` - Check if entity is locked

## SOE (Standards Overlay Engine)
- `POST /soe/evaluate` - Evaluate SOE rules and generate SOERun
- `POST /soe/explain` - Generate human-readable explanation for SOE decision
- `POST /soe/export-manifest` - Export audit manifest for SOE run
- `POST /soe/decision-log` - Create decision log with deterministic IDs

## Outputs (Execution Intent)
- `POST /outputs/{plan_id}/generate` - Generate execution outputs for plan
- `GET /outputs/{plan_id}` - Get execution outputs
- `POST /outputs/{plan_id}/export` - Export execution outputs (Sprint 3, approved plans only)

## Compliance (Sprint 4-5)
- `GET /compliance/plans/{plan_id}/compliance-trace` - Get compliance traceability for plan
- `GET /compliance/plans/{plan_id}/steps/{step_id}/compliance` - Get compliance trace for specific step
- `POST /compliance/plans/{plan_id}/reports/generate` - Generate compliance report (Sprint 5, approved plans only, HTML format)

## Profiles (Sprint 5) - Standards Profile Lifecycle, Versioning, and Bundles

### Profile Lifecycle
- `GET /profiles/{profile_id}/state` - Get current profile state
- `POST /profiles/{profile_id}/submit` - Submit profile for approval (draft → submitted, Ops/Admin)
- `POST /profiles/{profile_id}/approve` - Approve profile (submitted → approved, Ops/Admin)
- `POST /profiles/{profile_id}/reject` - Reject profile (submitted → draft, Ops/Admin)
- `POST /profiles/{profile_id}/deprecate` - Deprecate profile (approved → deprecated, Ops/Admin)
- `POST /profiles/{profile_id}/validate` - Validate profile for use in SOE runs

### Profile Versioning
- `POST /profiles/{profile_id}/versions` - Create new profile version (Ops/Admin)
- `GET /profiles/{profile_id}/versions` - List all versions of a profile
- `GET /profiles/{profile_id}/versions/{version}` - Get specific profile version
- `GET /profiles/{profile_id}/versions/compare` - Compare two profile versions

### Profile Bundles
- `POST /profiles/bundles` - Create profile bundle (Ops/Admin)
- `GET /profiles/bundles/{bundle_id}` - Get profile bundle
- `GET /profiles/bundles` - List all profile bundles

## Test Suites
- Contract Tests: `python services/api/scripts/agent_contract_tests.py`
- End-to-End Tests: `python services/api/scripts/e2e_test.py`
- Unit Tests: `pytest services/api/tests/`
- Schema Validation Tests: `pytest services/api/tests/test_schema_validation.py`
