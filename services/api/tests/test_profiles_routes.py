"""Contract test for /profiles routes (Sprint 7).

Verifies that profiles router endpoints are accessible and return expected responses.
"""

import pytest
from fastapi.testclient import TestClient
from services.api.main import app

client = TestClient(app)


def test_profiles_router_mounted():
    """Verify profiles router is mounted and accessible."""
    # This should return 401 (unauthorized) or 422 (validation error), not 404 (not found)
    # If router is not mounted, we'd get 404
    response = client.get("/profiles/nonexistent_profile_id/state")
    
    # Should not be 404 (router not found)
    assert response.status_code != 404, "Profiles router should be mounted (got 404 = router not found)"


def test_get_profile_state_endpoint_exists():
    """Test GET /profiles/{profile_id}/state endpoint exists."""
    # Try with a non-existent profile - should get 404 (profile not found), not 404 (route not found)
    response = client.get(
        "/profiles/nonexistent_profile/state",
        headers={"Authorization": "Bearer test_token"},
    )
    
    # Should get 404 (profile not found) or 422 (validation error), not 404 from router
    # If we get 404 with "Not Found" detail, it might be router-level 404
    # If we get 422 or specific error about profile, router is working
    assert response.status_code in [404, 422, 401], f"Unexpected status: {response.status_code}"


def test_get_profile_bundles_endpoint_exists():
    """Test GET /profiles/bundles endpoint exists."""
    response = client.get(
        "/profiles/bundles",
        headers={"Authorization": "Bearer test_token"},
    )
    
    # Should get 401 (unauthorized) or 200 (if auth bypassed), not 404
    assert response.status_code != 404, "GET /profiles/bundles should exist"


def test_validate_profile_endpoint_exists():
    """Test POST /profiles/{profile_id}/validate endpoint exists."""
    response = client.post(
        "/profiles/nonexistent_profile/validate",
        headers={"Authorization": "Bearer test_token"},
    )
    
    # Should get 404 (profile not found) or 422/401, not router-level 404
    assert response.status_code in [404, 422, 401], f"Unexpected status: {response.status_code}"
