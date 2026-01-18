# Testing Datum API

This document describes how to test the Datum API endpoints.

## Setup

1. Install dependencies:
```bash
cd services/api
pip install -r requirements.txt
```

2. Ensure storage directory exists:
```bash
mkdir -p storage/uploads
```

## Running Tests

### Unit Tests
```bash
# From repo root (recommended - uses conftest.py for import resolution)
pytest services/api/tests/ -v

# Or from services/api directory
cd services/api
PYTHONPATH=../.. pytest tests/ -v
```

**Note (Sprint 7):** Tests can now be run from repo root thanks to `services/api/conftest.py`, which adds the repo root to `sys.path` for `services` module imports.

### Contract Tests
```bash
python services/api/scripts/agent_contract_tests.py
```

### Schema Validation
```bash
python services/api/scripts/validate_schemas.py
```

### Red-team Checks
```bash
python services/api/scripts/redteam_checks.py
```

## Manual Testing

### 1. Start the API Server
```bash
cd services/api
uvicorn main:app --reload --port 8000
```

### 2. Get Auth Token
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "role": "CUSTOMER"}'
```

Save the `access_token` from the response.

### 3. Test Health Endpoint
```bash
curl http://localhost:8000/health
```

Expected: `{"status": "ok"}`

### 4. Test Gerber Upload

Create a test ZIP file with Gerber files:
```bash
# Create test ZIP
mkdir -p test_gerbers
echo "G04 Mock Gerber file*" > test_gerbers/board.gbr
echo "G04 Mock outline*" > test_gerbers/outline.gbr
zip -r test_gerbers.zip test_gerbers/
```

Upload:
```bash
curl -X POST http://localhost:8000/uploads/gerbers \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_gerbers.zip"
```

Expected: Returns `upload_id`, `sha256`, `files` list, and `created_at`

### 5. Test Board Metrics
```bash
# Replace UPLOAD_ID with the upload_id from step 4
curl http://localhost:8000/uploads/gerbers/UPLOAD_ID/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected: Returns `layer_count`, `width_mm`, `height_mm`, `area_mm2`, etc.

### 6. Test BOM Upload

Create test CSV:
```csv
RefDes,Qty,MPN,Manufacturer
R1,1,RES_10K,ResistorCo
C1,2,CAP_100uF,CapCo
U1,1,MCU_ATMEGA328,Microchip
```

Upload:
```bash
curl -X POST http://localhost:8000/uploads/bom \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_bom.csv"
```

Expected: Returns `upload_id`, `sha256`, `format`, `items` (normalized BOM)

### 7. Test Normalized BOM Retrieval
```bash
# Replace BOM_UPLOAD_ID with the upload_id from step 6
curl http://localhost:8000/uploads/bom/BOM_UPLOAD_ID/normalized \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected: Returns normalized BOM items

### 8. Test Quote Generation

**Note:** The quotes endpoint needs to be updated to use the new pricing module. Currently it returns placeholder data.

Once updated, test with:
```bash
curl -X POST http://localhost:8000/quotes/estimate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "gerber_upload_id": "GERBER_UPLOAD_ID",
    "bom_upload_id": "BOM_UPLOAD_ID",
    "quantity": 10,
    "assumptions": {"assembly_sides": ["TOP"]}
  }'
```

Expected: Returns full DatumQuote with:
- `cost_breakdown` with lines (PCB_FAB, ASSEMBLY_LABOR, COMPONENTS, etc.)
- `risk_factors` (from supply chain and DRC checks)
- `lead_time_days`
- `inputs_fingerprint`
- Validates against schema

## Test Coverage

### Implemented Endpoints
- ✅ `GET /health` - Health check
- ✅ `POST /auth/login` - Authentication
- ✅ `POST /uploads/gerbers` - Gerber ZIP upload with extraction
- ✅ `GET /uploads/gerbers/{upload_id}/metrics` - Board metrics
- ✅ `POST /uploads/bom` - BOM upload with normalization
- ✅ `GET /uploads/bom/{upload_id}/normalized` - Normalized BOM retrieval
- ⚠️ `POST /quotes/estimate` - **Needs update to use pricing module**

### Features Tested
- ✅ File upload and storage
- ✅ ZIP extraction and file cataloging
- ✅ Board metrics extraction (layer count, dimensions)
- ✅ BOM parsing and normalization (CSV/XLSX)
- ✅ Supply chain risk analysis
- ✅ DRC checks (drill-to-copper, copper-to-edge)
- ⚠️ Pricing calculation - **Integrated but quotes endpoint not updated**
- ✅ Schema validation

## Known Issues

1. **Quotes endpoint** (`/quotes/estimate`) still returns placeholder data. It needs to be updated to:
   - Accept `QuoteEstimateRequest` with `gerber_upload_id` and `bom_upload_id`
   - Fetch board metrics and normalized BOM
   - Call `calculate_pricing()` with full inputs
   - Include DRC checks and supply chain risks
   - Return proper DatumQuote with risk factors

2. **Storage persistence** - Currently files are stored in `storage/uploads/`. In production, this should use a proper storage backend (S3, etc.)

3. **Component pricing** - Currently uses placeholder values. Real implementation would query vendor APIs.

4. **Lead time lookup** - Currently uses placeholder heuristics. Real implementation would query vendor databases.
