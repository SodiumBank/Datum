"""Tests for upload endpoints."""

import io
import zipfile
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.core.security import sign_token

client = TestClient(app)


def _get_auth_token(role: str = "CUSTOMER") -> str:
    """Get auth token for testing."""
    response = client.post("/auth/login", json={"user_id": "test_user", "role": role})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_upload_gerbers():
    """Test Gerber ZIP upload endpoint."""
    token = _get_auth_token()
    
    # Create a test ZIP file with mock Gerber files
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("board.gbr", "G04 Mock Gerber file*\n")
        zip_file.writestr("board_outline.gbr", "G04 Mock outline*\n")
        zip_file.writestr("board.drl", "G04 Mock drill file*\n")
    zip_buffer.seek(0)
    
    # Upload
    response = client.post(
        "/uploads/gerbers",
        files={"file": ("test_gerbers.zip", zip_buffer, "application/zip")},
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "upload_id" in data
    assert "sha256" in data
    assert "files" in data
    assert len(data["files"]) == 3
    assert data["files"][0]["type"] in ["GERBER", "EXCELLON", "OTHER"]
    
    # Test metrics endpoint
    upload_id = data["upload_id"]
    response = client.get(
        f"/uploads/gerbers/{upload_id}/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    metrics = response.json()
    assert "layer_count" in metrics
    assert "upload_id" in metrics


def test_upload_bom_csv():
    """Test BOM CSV upload endpoint."""
    token = _get_auth_token()
    
    # Create test CSV
    csv_content = "RefDes,Qty,MPN,Manufacturer\nR1,1,RES_10K,ResistorCo\nC1,2,CAP_100uF,CapCo\n"
    csv_file = io.BytesIO(csv_content.encode("utf-8"))
    
    # Upload
    response = client.post(
        "/uploads/bom",
        files={"file": ("test_bom.csv", csv_file, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "upload_id" in data
    assert "sha256" in data
    assert "format" in data
    assert data["format"] == "CSV"
    assert "items" in data
    assert len(data["items"]) == 2
    
    # Verify normalized BOM
    assert data["items"][0]["refdes"] == "R1"
    assert data["items"][0]["qty"] == 1
    assert data["items"][0]["mpn"] == "RES_10K"
    
    # Test normalized BOM retrieval
    upload_id = data["upload_id"]
    response = client.get(
        f"/uploads/bom/{upload_id}/normalized",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    bom_data = response.json()
    assert "items" in bom_data
    assert len(bom_data["items"]) == 2


def test_upload_gerbers_invalid_file():
    """Test Gerber upload with invalid file type."""
    token = _get_auth_token()
    
    # Upload non-ZIP file
    response = client.post(
        "/uploads/gerbers",
        files={"file": ("test.txt", io.BytesIO(b"not a zip"), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 400


def test_upload_bom_invalid_file():
    """Test BOM upload with invalid file type."""
    token = _get_auth_token()
    
    # Upload non-CSV/XLSX file
    response = client.post(
        "/uploads/bom",
        files={"file": ("test.txt", io.BytesIO(b"not a bom"), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 400


def test_unauthorized_access():
    """Test that endpoints require authentication."""
    # Try without token
    response = client.post("/uploads/gerbers", files={"file": ("test.zip", io.BytesIO(), "application/zip")})
    assert response.status_code == 401
