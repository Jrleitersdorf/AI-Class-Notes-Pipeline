"""Tests for src/granola_sync/state.py"""
import json

import pytest

from granola_sync.state import is_synced, load_state, mark_synced, save_state


@pytest.fixture
def state_file(tmp_path):
    return str(tmp_path / ".state.json")


def test_load_state_missing_file_returns_empty(state_file):
    assert load_state(state_file) == {}


def test_save_and_load_round_trip(state_file):
    state = {"not_abc": "2026-01-01T00:00:00Z"}
    save_state(state, state_file)
    loaded = load_state(state_file)
    assert loaded == state


def test_mark_synced_mutates_in_place(state_file):
    state = {}
    mark_synced("not_abc", "2026-01-01T00:00:00Z", state)
    assert state["not_abc"] == "2026-01-01T00:00:00Z"


def test_is_synced_match(state_file):
    state = {"not_abc": "2026-01-01T00:00:00Z"}
    assert is_synced("not_abc", "2026-01-01T00:00:00Z", state) is True


def test_is_synced_timestamp_mismatch(state_file):
    state = {"not_abc": "2026-01-01T00:00:00Z"}
    assert is_synced("not_abc", "2026-01-02T00:00:00Z", state) is False


def test_is_synced_missing_note(state_file):
    assert is_synced("not_missing", "2026-01-01T00:00:00Z", {}) is False


def test_save_state_creates_parent_dirs(tmp_path):
    nested = str(tmp_path / "a" / "b" / ".state.json")
    save_state({"not_x": "2026-01-01T00:00:00Z"}, nested)
    assert json.loads(open(nested).read()) == {"not_x": "2026-01-01T00:00:00Z"}
