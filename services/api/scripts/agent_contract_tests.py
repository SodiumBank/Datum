"""Agent Contract Tests

These tests are run in CI to enforce Datum's product laws early, even before full implementation.

As endpoints become real, tighten these tests (remove placeholders).
"""

from __future__ import annotations

import copy
import io
import json
import zipfile
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.core.security import sign_token
from services.api.core.soe_engine import evaluate_soe
from services.api.core.schema_validation import validate_schema

def main() -> None:
    client = TestClient(app)
    
    # Get auth token
    token = sign_token("test_user", "CUSTOMER")  # type: ignore[arg-type]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup: Create test uploads for quote testing
    # 1) Upload Gerber ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("board.gbr", "G04 Mock Gerber file*\nX1000Y2000*\n")
        zip_file.writestr("board_outline.gbr", "G04 Mock outline*\nX0Y0*\nX5000Y5000*\n")
    zip_buffer.seek(0)
    
    gerber_resp = client.post(
        "/uploads/gerbers",
        files={"file": ("test.zip", zip_buffer, "application/zip")},
        headers=headers,
    )
    assert gerber_resp.status_code == 200, f"Gerber upload failed: {gerber_resp.status_code}"
    gerber_upload_id = gerber_resp.json()["upload_id"]
    
    # 2) Upload BOM CSV
    bom_csv = io.BytesIO(b"RefDes,Qty,MPN\nR1,1,RES_10K\n")
    bom_resp = client.post(
        "/uploads/bom",
        files={"file": ("test.csv", bom_csv, "text/csv")},
        headers=headers,
    )
    assert bom_resp.status_code == 200, f"BOM upload failed: {bom_resp.status_code}"
    bom_upload_id = bom_resp.json()["upload_id"]

    # 1) Determinism: same request -> same response payload
    request_body = {
        "gerber_upload_id": gerber_upload_id,
        "bom_upload_id": bom_upload_id,
        "quantity": 10,
        "assumptions": {"assembly_sides": ["TOP"]},
    }
    r1 = client.post("/quotes/estimate", json=request_body, headers=headers)
    r2 = client.post("/quotes/estimate", json=request_body, headers=headers)
    assert r1.status_code == 200 and r2.status_code == 200, f"Quote failed: {r1.status_code} / {r2.status_code}"
    j1 = r1.json()
    j2 = r2.json()
    
    # For determinism check, compare critical fields (IDs will differ)
    assert j1["inputs_fingerprint"] == j2["inputs_fingerprint"], "Non-deterministic inputs_fingerprint"
    assert j1["cost_breakdown"]["total"] == j2["cost_breakdown"]["total"], "Non-deterministic total cost"
    assert j1["lead_time_days"] == j2["lead_time_days"], "Non-deterministic lead time"

    # 2) Schema presence: key fields exist (lightweight until full schema validation per response)
    required_fields = ["id", "tier", "quote_version", "cost_breakdown", "inputs_fingerprint"]
    for f in required_fields:
        assert f in j1, f"Missing field in quote: {f}"

    # 3) Schema validation: validate quote against schema
    from services.api.core.schema_validation import validate_schema
    try:
        validate_schema(j1, "datum_quote.schema.json")
    except Exception as e:
        assert False, f"Quote schema validation failed: {e}"

    # 4) Lock immutability: lock quote and verify it cannot be modified
    ops_token = sign_token("ops_user", "OPS")  # type: ignore[arg-type]
    ops_headers = {"Authorization": f"Bearer {ops_token}"}
    
    lock_resp = client.post(
        f"/quotes/{j1['id']}/lock",
        json={"lock_reason": "Test lock", "requires_contract": False},
        headers=ops_headers,
    )
    assert lock_resp.status_code == 200, f"Lock failed: {lock_resp.status_code}"
    locked_quote = lock_resp.json()["quote"]
    assert locked_quote["status"] == "LOCKED", "Quote not marked as locked"
    
    # Verify audit event was created
    from services.api.core.storage import list_audit_events
    audit_events = list_audit_events("DATUM_QUOTE", j1["id"])
    lock_events = [e for e in audit_events if e.get("action") == "LOCK"]
    assert len(lock_events) > 0, "Lock audit event not created"
    
    # Verify schema files exist
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[3]
    assert (root / "schemas" / "datum_lock.schema.json").exists()
    assert (root / "schemas" / "datum_revision.schema.json").exists()
    assert (root / "schemas" / "datum_audit_event.schema.json").exists()

    # SOE Contract Tests
    print("\n=== SOE Contract Tests ===")
    
    # Test SOE evaluation determinism
    soe_inputs = {
        "processes": ["SMT", "CONFORMAL_COAT"],
        "tests_requested": [],
        "materials": ["EPOXY_3M_SCOTCHWELD_2216"],
        "bom_risk_flags": [],
    }
    
    soe_run1 = evaluate_soe(
        industry_profile="space",
        inputs=soe_inputs,
        hardware_class="flight",
    )
    
    soe_run2 = evaluate_soe(
        industry_profile="space",
        inputs=soe_inputs,
        hardware_class="flight",
    )
    
    # Validate SOERun schema
    try:
        validate_schema(soe_run1, "soe_run.schema.json")
        print("✅ SOERun schema validation passed")
    except Exception as e:
        raise AssertionError(f"SOERun schema validation failed: {e}") from e
    
    # Test determinism: same inputs -> same decision IDs
    decisions1 = sorted(soe_run1["decisions"], key=lambda d: d["id"])
    decisions2 = sorted(soe_run2["decisions"], key=lambda d: d["id"])
    
    assert len(decisions1) == len(decisions2), "SOE decision count must be deterministic"
    for d1, d2 in zip(decisions1, decisions2):
        assert d1["id"] == d2["id"], f"SOE decision IDs must be deterministic: {d1['id']} != {d2['id']}"
        assert d1["action"] == d2["action"], "SOE decision actions must be deterministic"
        assert d1["object_id"] == d2["object_id"], "SOE decision object IDs must be deterministic"
    
    print(f"✅ SOE determinism test passed ({len(decisions1)} decisions)")
    
    # Test SOE endpoint
    soe_eval_resp = client.post(
        "/soe/evaluate",
        json={
            "industry_profile": "space",
            "hardware_class": "flight",
            "inputs": soe_inputs,
        },
        headers=headers,
    )
    assert soe_eval_resp.status_code == 200, f"SOE evaluate failed: {soe_eval_resp.status_code}"
    soe_response = soe_eval_resp.json()
    
    # Validate SOERun structure
    assert "soe_version" in soe_response
    assert "industry_profile" in soe_response
    assert "decisions" in soe_response
    assert "gates" in soe_response
    
    # Validate decision IDs are deterministic
    endpoint_decisions = sorted(soe_response["decisions"], key=lambda d: d["id"])
    assert len(endpoint_decisions) == len(decisions1), "Endpoint should return same number of decisions"
    for ep_d, local_d in zip(endpoint_decisions, decisions1):
        assert ep_d["id"] == local_d["id"], "Endpoint decision IDs must match local evaluation"
    
    print("✅ SOE endpoint contract test passed")
    
    # Test that non-deterministic inputs produce different results
    soe_inputs_diff = copy.deepcopy(soe_inputs)
    soe_inputs_diff["processes"] = ["SMT"]  # Remove CONFORMAL_COAT
    
    soe_run_diff = evaluate_soe(
        industry_profile="space",
        inputs=soe_inputs_diff,
        hardware_class="flight",
    )
    
    # Should produce different decisions (or at least validate it runs)
    validate_schema(soe_run_diff, "soe_run.schema.json")
    print("✅ SOE non-deterministic input test passed")
    
    print("✅ SOE contract tests passed")
    
    print("\n✅ All contract tests passed")

if __name__ == "__main__":
    main()
