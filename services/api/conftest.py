"""Pytest configuration and fixtures for Datum API tests.

This conftest.py ensures tests can import from services.api when run from repo root.
"""

import sys
from pathlib import Path

# Add repo root to sys.path for imports
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
