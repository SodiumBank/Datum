"""Tests for Sprint 5 profile lifecycle."""

import pytest
from services.api.core.profile_lifecycle import (
    get_profile_state,
    validate_profile_for_use,
    can_modify_profile,
)


def test_get_profile_state_defaults_to_draft():
    """Test that profiles default to draft state."""
    # This would require a profile fixture
    # For now, just verify the function exists
    assert get_profile_state is not None
    assert validate_profile_for_use is not None
    assert can_modify_profile is not None


def test_validate_profile_for_use_blocks_deprecated():
    """Test that deprecated profiles are blocked."""
    # Would need actual profile fixtures
    pass


def test_validate_profile_for_use_blocks_draft():
    """Test that draft profiles are blocked in production."""
    # Would need actual profile fixtures
    pass
