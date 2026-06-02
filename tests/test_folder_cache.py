"""Tests for src/granola_sync/folder_cache.py"""
import json
from unittest.mock import MagicMock

import pytest

from granola_sync.folder_cache import (
    load_folder_cache,
    refresh_folder_cache,
    save_folder_cache,
)


@pytest.fixture
def cache_file(tmp_path):
    return str(tmp_path / ".folders.json")


# ---------------------------------------------------------------------------
# load_folder_cache
# ---------------------------------------------------------------------------

def test_load_returns_empty_when_missing(cache_file):
    result = load_folder_cache(cache_file)
    assert result == {"folders": [], "refreshed_at": None}


def test_load_returns_empty_when_corrupted(cache_file):
    with open(cache_file, "w") as f:
        f.write("not valid json {{{")
    # Corrupted cache must degrade gracefully — same shape as missing
    assert load_folder_cache(cache_file) == {"folders": [], "refreshed_at": None}


def test_load_returns_empty_when_missing_keys(cache_file):
    """A cache file that exists but lacks the expected keys still returns the empty shape."""
    with open(cache_file, "w") as f:
        json.dump({}, f)
    assert load_folder_cache(cache_file) == {"folders": [], "refreshed_at": None}


# ---------------------------------------------------------------------------
# save_folder_cache + round-trip
# ---------------------------------------------------------------------------

def test_save_writes_folders_and_timestamp(cache_file):
    folders = [
        {"id": "fol_aaa", "object": "folder", "name": "CS101"},
        {"id": "fol_bbb", "object": "folder", "name": "Algorithms"},
    ]
    refreshed_at = save_folder_cache(folders, cache_file)
    assert isinstance(refreshed_at, str) and len(refreshed_at) > 0

    raw = json.loads(open(cache_file).read())
    assert raw["folders"] == folders
    assert raw["refreshed_at"] == refreshed_at


def test_save_load_round_trip(cache_file):
    folders = [{"id": "fol_x", "object": "folder", "name": "Test"}]
    save_folder_cache(folders, cache_file)
    loaded = load_folder_cache(cache_file)
    assert loaded["folders"] == folders
    assert loaded["refreshed_at"] is not None


def test_save_creates_parent_dirs(tmp_path):
    nested = str(tmp_path / "deep" / "nested" / ".folders.json")
    save_folder_cache([{"id": "fol_x", "name": "Test"}], nested)
    assert load_folder_cache(nested)["folders"] == [{"id": "fol_x", "name": "Test"}]


def test_save_overwrites_existing_cache(cache_file):
    save_folder_cache([{"id": "fol_old", "name": "Old"}], cache_file)
    save_folder_cache([{"id": "fol_new", "name": "New"}], cache_file)
    assert load_folder_cache(cache_file)["folders"] == [{"id": "fol_new", "name": "New"}]


# ---------------------------------------------------------------------------
# refresh_folder_cache
# ---------------------------------------------------------------------------

def test_refresh_calls_client_and_saves(cache_file):
    folders = [{"id": "fol_x", "object": "folder", "name": "CS101"}]
    client = MagicMock()
    client.list_folders.return_value = folders

    result = refresh_folder_cache(client, cache_file)

    client.list_folders.assert_called_once_with()
    assert result["folders"] == folders
    assert result["refreshed_at"] is not None
    # Verify it was actually persisted, not just returned
    assert load_folder_cache(cache_file)["folders"] == folders


def test_refresh_propagates_client_errors(cache_file):
    """If the API call fails, the cache is left untouched."""
    save_folder_cache([{"id": "fol_old", "name": "Old"}], cache_file)
    client = MagicMock()
    client.list_folders.side_effect = RuntimeError("API down")

    with pytest.raises(RuntimeError, match="API down"):
        refresh_folder_cache(client, cache_file)

    # Existing cache is preserved
    assert load_folder_cache(cache_file)["folders"] == [{"id": "fol_old", "name": "Old"}]
