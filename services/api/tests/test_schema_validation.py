"""Schema validation tests for all generated objects."""

from fastapi.testclient import TestClient
from services.api.main import app
from services.api.core.security import sign_token
from services.api.core.schema_validation import validate_schema
import io
import zipfile


def test_quote_schema_validation():
    """Test that quotes validate against schema."""
    client = TestClient(app)
    
    token = sign_token("test_user", "CUSTOMER")  # type: ignore[arg-type]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup: Upload files
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("board.gbr", "G04 Mock Gerber*\nM02*\n")
        zip_file.writestr("board_outline.gbr", "G04 Mock outline*\nM02*\n")
    zip_buffer.seek(0)
    
    gerber_resp = client.post(
        "/uploads/gerbers",
        files={"file": ("test.zip", zip_buffer, "application/zip")},
        headers=headers,
    )
    assert gerber_resp.status_code == 200
    gerber_upload_id = gerber_resp.json()["upload_id"]
    
    bom_csv = io.BytesIO(b"RefDes,Qty,MPN\nR1,1,RES_10K\n")
    bom_resp = client.post(
        "/uploads/bom",
        files={"file": ("test.csv", bom_csv, "text/csv")},
        headers=headers,
    )
    assert bom_resp.status_code == 200
    bom_upload_id = bom_resp.json()["upload_id"]
    
    # Generate quote
    quote_resp = client.post(
        "/quotes/estimate",
        json={
            "gerber_upload_id": gerber_upload_id,
            "bom_upload_id": bom_upload_id,
            "quantity": 1,
        },
        headers=headers,
    )
    assert quote_resp.status_code == 200
    quote = quote_resp.json()
    
    # Validate schema
    try:
        validate_schema(quote, "datum_quote.schema.json")
    except Exception as e:
        assert False, f"Quote schema validation failed: {e}"


def test_plan_schema_validation():
    """Test that plans validate against schema."""
    client = TestClient(app)
    
    token = sign_token("test_user", "CUSTOMER")  # type: ignore[arg-type]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup: Create quote first
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("board.gbr", "G04 Mock Gerber*\nM02*\n")
        zip_file.writestr("board_outline.gbr", "G04 Mock outline*\nM02*\n")
    zip_buffer.seek(0)
    
    gerber_resp = client.post(
        "/uploads/gerbers",
        files={"file": ("test.zip", zip_buffer, "application/zip")},
        headers=headers,
    )
    assert gerber_resp.status_code == 200
    gerber_upload_id = gerber_resp.json()["upload_id"]
    
    bom_csv = io.BytesIO(b"RefDes,Qty,MPN\nR1,1,RES_10K\n")
    bom_resp = client.post(
        "/uploads/bom",
        files={"file": ("test.csv", bom_csv, "text/csv")},
        headers=headers,
    )
    assert bom_resp.status_code == 200
    bom_upload_id = bom_resp.json()["upload_id"]
    
    quote_resp = client.post(
        "/quotes/estimate",
        json={
            "gerber_upload_id": gerber_upload_id,
            "bom_upload_id": bom_upload_id,
            "quantity": 1,
        },
        headers=headers,
    )
    assert quote_resp.status_code == 200
    quote_id = quote_resp.json()["id"]
    
    # Generate plan
    plan_resp = client.post(
        "/plans/generate",
        json={"quote_id": quote_id},
        headers=headers,
    )
    assert plan_resp.status_code == 200
    plan = plan_resp.json()
    
    # Validate schema
    try:
        validate_schema(plan, "datum_plan.schema.json")
    except Exception as e:
        assert False, f"Plan schema validation failed: {e}"


def test_tests_schema_validation():
    """Test that tests declarations validate against schema."""
    client = TestClient(app)
    
    token = sign_token("test_user", "CUSTOMER")  # type: ignore[arg-type]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup: Create quote and plan first
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("board.gbr", "G04 Mock Gerber*\nM02*\n")
        zip_file.writestr("board_outline.gbr", "G04 Mock outline*\nM02*\n")
    zip_buffer.seek(0)
    
    gerber_resp = client.post(
        "/uploads/gerbers",
        files={"file": ("test.zip", zip_buffer, "application/zip")},
        headers=headers,
    )
    assert gerber_resp.status_code == 200
    gerber_upload_id = gerber_resp.json()["upload_id"]
    
    bom_csv = io.BytesIO(b"RefDes,Qty,MPN\nR1,1,RES_10K\n")
    bom_resp = client.post(
        "/uploads/bom",
        files={"file": ("test.csv", bom_csv, "text/csv")},
        headers=headers,
    )
    assert bom_resp.status_code == 200
    bom_upload_id = bom_resp.json()["upload_id"]
    
    quote_resp = client.post(
        "/quotes/estimate",
        json={
            "gerber_upload_id": gerber_upload_id,
            "bom_upload_id": bom_upload_id,
            "quantity": 1,
        },
        headers=headers,
    )
    assert quote_resp.status_code == 200
    quote_id = quote_resp.json()["id"]
    
    plan_resp = client.post(
        "/plans/generate",
        json={"quote_id": quote_id},
        headers=headers,
    )
    assert plan_resp.status_code == 200
    plan_id = plan_resp.json()["id"]
    
    # Generate tests
    tests_resp = client.post(
        "/tests/generate",
        json={"plan_id": plan_id},
        headers=headers,
    )
    assert tests_resp.status_code == 200
    tests = tests_resp.json()
    
    # Validate schema
    try:
        validate_schema(tests, "datum_tests.schema.json")
    except Exception as e:
        assert False, f"Tests schema validation failed: {e}"
