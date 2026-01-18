"""Smoke test: Import services.api.main and verify app exists (Sprint 7).

This test catches regressions early if the app structure breaks.
"""

import pytest


def test_import_main():
    """Test that services.api.main can be imported and app exists."""
    import services.api.main
    
    assert hasattr(services.api.main, "app"), "services.api.main must have 'app' attribute"
    assert services.api.main.app is not None, "app must not be None"
    
    # Verify it's a FastAPI app (basic check)
    assert hasattr(services.api.main.app, "router"), "app should have router attribute (FastAPI app)"


def test_main_app_title():
    """Test that app has expected metadata."""
    import services.api.main
    
    app = services.api.main.app
    assert app.title == "Datum API", "App title should be 'Datum API'"
    assert app.version == "0.1.0", "App version should be '0.1.0'"
