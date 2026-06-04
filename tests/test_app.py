"""Tests for src/granola_sync/app.py — the JS↔Python bridge."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from granola_sync import app as app_module
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

def test_find_frontend_index_editable_path_lands_inside_repo(tmp_path, monkeypatch):
    """
    Regression for the off-by-one in `_find_frontend_index()`:
    the editable-install candidate must resolve to <repo>/frontend/dist/index.html,
    not one level above the repo.
    """
    # Create a fake editable layout: tmp_path/src/granola_sync/app.py
    fake_pkg = tmp_path / "src" / "granola_sync"
    fake_pkg.mkdir(parents=True)
    fake_file = fake_pkg / "app.py"
    fake_file.write_text("# stub")

    # Create the frontend/dist/index.html where the helper SHOULD find it
    frontend_index = tmp_path / "frontend" / "dist" / "index.html"
    frontend_index.parent.mkdir(parents=True)
    frontend_index.write_text("<!doctype html>")

    # Monkeypatch the module's __file__ so _find_frontend_index resolves against our fake tree
    monkeypatch.setattr(app_module, "__file__", str(fake_file))

    found = app_module._find_frontend_index()
    assert found is not None, "helper returned None — path math is wrong"
    assert found == frontend_index, (
        f"editable-install candidate resolved to {found}, "
        f"expected {frontend_index}"
    )
