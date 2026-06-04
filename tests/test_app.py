"""Tests for src/granola_sync/app.py — the JS↔Python bridge."""
from unittest.mock import MagicMock, patch

import pytest

from granola_sync.app import Api


@pytest.fixture
def api():
    return Api()


# ---------------------------------------------------------------------------
# get_version
# ---------------------------------------------------------------------------

def test_get_version_returns_string(api):
    v = api.get_version()
    assert isinstance(v, str) and len(v) > 0
    assert v.count(".") >= 2          # x.y.z
