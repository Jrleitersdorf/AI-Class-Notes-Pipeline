"""Tests for src/granola_sync/mappings.py"""
import json
import os
import tempfile

import pytest

from granola_sync.mappings import (
    create_mapping,
    delete_mapping,
    get_api_key,
    get_mapping,
    list_mappings,
    set_api_key,
    update_mapping,
)


@pytest.fixture
def cfg(tmp_path):
    """Return a temp config path that does not yet exist."""
    return str(tmp_path / "config.json")


# ---------------------------------------------------------------------------
# create_mapping
# ---------------------------------------------------------------------------

def test_create_mapping_returns_dict(cfg):
    m = create_mapping("fol_aaa", "CS101", "/tmp/notes", config_path=cfg)
    assert m["folder_id"] == "fol_aaa"
    assert m["folder_name"] == "CS101"
    assert m["local_path"] == "/tmp/notes"


def test_create_mapping_persists(cfg):
    create_mapping("fol_aaa", "CS101", "/tmp/notes", config_path=cfg)
    data = json.loads(open(cfg).read())
    assert len(data["mappings"]) == 1
    assert data["mappings"][0]["folder_id"] == "fol_aaa"


def test_create_mapping_duplicate_raises(cfg):
    create_mapping("fol_aaa", "CS101", "/tmp/a", config_path=cfg)
    with pytest.raises(ValueError, match="already exists"):
        create_mapping("fol_aaa", "CS101", "/tmp/b", config_path=cfg)


def test_create_multiple_mappings(cfg):
    create_mapping("fol_aaa", "CS101", "/tmp/a", config_path=cfg)
    create_mapping("fol_bbb", "CS202", "/tmp/b", config_path=cfg)
    assert len(list_mappings(config_path=cfg)) == 2


# ---------------------------------------------------------------------------
# list_mappings
# ---------------------------------------------------------------------------

def test_list_mappings_empty_when_no_file(cfg):
    assert list_mappings(config_path=cfg) == []


def test_list_mappings_empty_when_file_has_no_key(cfg):
    with open(cfg, "w") as f:
        json.dump({"granola_api_key": "grn_x"}, f)
    assert list_mappings(config_path=cfg) == []


# ---------------------------------------------------------------------------
# get_mapping
# ---------------------------------------------------------------------------

def test_get_mapping_found(cfg):
    create_mapping("fol_aaa", "CS101", "/tmp/a", config_path=cfg)
    m = get_mapping("fol_aaa", config_path=cfg)
    assert m is not None
    assert m["folder_id"] == "fol_aaa"


def test_get_mapping_not_found_returns_none(cfg):
    assert get_mapping("fol_ghost", config_path=cfg) is None


# ---------------------------------------------------------------------------
# update_mapping
# ---------------------------------------------------------------------------

def test_update_mapping_local_path(cfg):
    create_mapping("fol_aaa", "CS101", "/tmp/old", config_path=cfg)
    updated = update_mapping("fol_aaa", local_path="/tmp/new", config_path=cfg)
    assert updated["local_path"] == "/tmp/new"
    assert get_mapping("fol_aaa", config_path=cfg)["local_path"] == "/tmp/new"


def test_update_mapping_folder_name(cfg):
    create_mapping("fol_aaa", "Old Name", "/tmp/a", config_path=cfg)
    updated = update_mapping("fol_aaa", folder_name="New Name", config_path=cfg)
    assert updated["folder_name"] == "New Name"


def test_update_mapping_not_found_raises(cfg):
    with pytest.raises(KeyError):
        update_mapping("fol_ghost", local_path="/tmp/x", config_path=cfg)


# ---------------------------------------------------------------------------
# delete_mapping
# ---------------------------------------------------------------------------

def test_delete_mapping_returns_true(cfg):
    create_mapping("fol_aaa", "CS101", "/tmp/a", config_path=cfg)
    assert delete_mapping("fol_aaa", config_path=cfg) is True
    assert list_mappings(config_path=cfg) == []


def test_delete_mapping_not_found_returns_false(cfg):
    assert delete_mapping("fol_ghost", config_path=cfg) is False


def test_delete_mapping_preserves_others(cfg):
    create_mapping("fol_aaa", "CS101", "/tmp/a", config_path=cfg)
    create_mapping("fol_bbb", "CS202", "/tmp/b", config_path=cfg)
    delete_mapping("fol_aaa", config_path=cfg)
    remaining = list_mappings(config_path=cfg)
    assert len(remaining) == 1
    assert remaining[0]["folder_id"] == "fol_bbb"


# ---------------------------------------------------------------------------
# API key helpers
# ---------------------------------------------------------------------------

def test_set_and_get_api_key(cfg):
    set_api_key("grn_testkey", config_path=cfg)
    assert get_api_key(config_path=cfg) == "grn_testkey"


def test_get_api_key_none_when_missing(cfg):
    assert get_api_key(config_path=cfg) is None


def test_create_mapping_preserves_api_key(cfg):
    set_api_key("grn_testkey", config_path=cfg)
    create_mapping("fol_aaa", "CS101", "/tmp/a", config_path=cfg)
    assert get_api_key(config_path=cfg) == "grn_testkey"
