"""Tests for src/granola_sync/app.py — the JS↔Python bridge."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import webview

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


# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------

def test_set_and_get_api_key_roundtrip(api, tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH", str(cfg))
    assert api.get_api_key() is None
    api.set_api_key("grn_testkey")
    assert api.get_api_key() == "grn_testkey"


# ---------------------------------------------------------------------------
# Folder cache
# ---------------------------------------------------------------------------

def test_load_cached_folders_empty_when_missing(api, tmp_path, monkeypatch):
    monkeypatch.setattr("granola_sync.folder_cache._DEFAULT_CACHE_PATH",
                        str(tmp_path / ".folders.json"))
    result = api.load_cached_folders()
    assert result == {"folders": [], "refreshed_at": None}


def test_refresh_folders_calls_client_and_saves(api, tmp_path, monkeypatch):
    cache = tmp_path / ".folders.json"
    monkeypatch.setattr("granola_sync.folder_cache._DEFAULT_CACHE_PATH", str(cache))
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH",
                        str(tmp_path / "config.json"))
    api.set_api_key("grn_testkey")

    folders = [{"id": "fol_x", "object": "folder", "name": "CS101"}]
    with patch("granola_sync.app.GranolaClient") as ClientCls:
        ClientCls.return_value.list_folders.return_value = folders
        result = api.refresh_folders()

    assert result["folders"] == folders
    assert result["refreshed_at"] is not None


def test_refresh_folders_no_api_key_raises(api, tmp_path, monkeypatch):
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH",
                        str(tmp_path / "config.json"))
    with pytest.raises(RuntimeError, match="No API key"):
        api.refresh_folders()


# ---------------------------------------------------------------------------
# Mappings
# ---------------------------------------------------------------------------

def test_list_create_update_delete_mapping(api, tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH", str(cfg))

    assert api.list_mappings() == []

    m = api.create_mapping("fol_a", "CS101", str(tmp_path / "CS101"))
    assert m["extract"] == "both"

    m2 = api.update_mapping("fol_a", extract="ai_notes")
    assert m2["extract"] == "ai_notes"

    assert api.delete_mapping("fol_a") is True
    assert api.list_mappings() == []


def test_create_mapping_accepts_extract(api, tmp_path, monkeypatch):
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH",
                        str(tmp_path / "config.json"))
    m = api.create_mapping("fol_a", "CS101", str(tmp_path / "CS101"),
                           extract="transcript")
    assert m["extract"] == "transcript"


# ---------------------------------------------------------------------------
# pick_folder
# ---------------------------------------------------------------------------

def test_pick_folder_returns_path(api):
    fake_window = MagicMock()
    fake_window.create_file_dialog.return_value = ("/Users/x/Notes/CS101",)
    with patch.object(webview, "windows", [fake_window]):
        result = api.pick_folder()
    assert result == "/Users/x/Notes/CS101"


def test_pick_folder_returns_none_on_cancel(api):
    fake_window = MagicMock()
    fake_window.create_file_dialog.return_value = None
    with patch.object(webview, "windows", [fake_window]):
        assert api.pick_folder() is None


def test_pick_folder_no_window_returns_none(api):
    with patch.object(webview, "windows", []):
        assert api.pick_folder() is None


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

def test_sync_dry_run_returns_serializable_results(api, tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH", str(cfg))
    # No mappings configured → empty list
    assert api.sync_dry_run() == []


def test_start_sync_returns_sync_id_and_streams_done(api, tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH", str(cfg))
    monkeypatch.setattr("granola_sync.state._DEFAULT_STATE_PATH",
                        str(tmp_path / ".state.json"))
    api.set_api_key("grn_testkey")
    fake_window = MagicMock()
    with patch.object(webview, "windows", [fake_window]):
        sync_id = api.start_sync()
    assert isinstance(sync_id, str) and len(sync_id) > 0

    # The runner should have emitted a 'done' event with 0 counts
    import time
    deadline = time.time() + 2.0
    while time.time() < deadline:
        if any('"type": "done"' in c[0][0]
               for c in fake_window.evaluate_js.call_args_list):
            return
        time.sleep(0.02)
    pytest.fail("sync 'done' event was not emitted in 2s")


def test_start_sync_no_window_raises(api):
    with patch.object(webview, "windows", []):
        with pytest.raises(RuntimeError, match="No webview window available"):
            api.start_sync()


def test_cancel_sync_returns_bool(api):
    fake_window = MagicMock()
    with patch.object(webview, "windows", [fake_window]):
        # Cancelling an unknown sync_id returns False
        assert api.cancel_sync("not-a-real-id") is False
