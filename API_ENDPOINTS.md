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
- `POST /plans/{plan_id}/steps` - Update plan steps (with locked sequence validation)

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

## Test Suites
- Contract Tests: `python services/api/scripts/agent_contract_tests.py`
- End-to-End Tests: `python services/api/scripts/e2e_test.py`
- Unit Tests: `pytest services/api/tests/`
- Schema Validation Tests: `pytest services/api/tests/test_schema_validation.py`
