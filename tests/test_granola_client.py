"""Tests for src/granola_sync/granola_client.py"""
from unittest.mock import MagicMock, patch

import pytest

from granola_sync.granola_client import GranolaAPIError, GranolaClient


@pytest.fixture
def client():
    return GranolaClient("grn_testkey")


# ---------------------------------------------------------------------------
# GranolaAPIError
# ---------------------------------------------------------------------------

def test_api_error_stores_status_code():
    err = GranolaAPIError(401, "Unauthorized")
    assert err.status_code == 401
    assert "401" in str(err)


# ---------------------------------------------------------------------------
# _get — error handling & retry
# ---------------------------------------------------------------------------

def _make_resp(status, body=None, json_data=None):
    resp = MagicMock()
    resp.status_code = status
    resp.ok = (200 <= status < 300)
    resp.text = body or ""
    resp.json.return_value = json_data or {}
    return resp


def test_get_raises_on_4xx(client):
    with patch.object(client._session, "get", return_value=_make_resp(401, "Unauthorized")):
        with pytest.raises(GranolaAPIError) as exc_info:
            client._get("/v1/notes")
    assert exc_info.value.status_code == 401


def test_get_retries_once_on_429(client):
    call_count = {"n": 0}
    def side_effect(url, params):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _make_resp(429, "rate limited")
        return _make_resp(200, json_data={"notes": [], "hasMore": False, "cursor": None})

    with patch.object(client._session, "get", side_effect=side_effect):
        result = client._get("/v1/notes")
    assert call_count["n"] == 2
    assert result == {"notes": [], "hasMore": False, "cursor": None}


def test_get_raises_after_persistent_429(client):
    with patch.object(client._session, "get", return_value=_make_resp(429, "still limited")):
        with pytest.raises(GranolaAPIError) as exc_info:
            client._get("/v1/notes")
    assert exc_info.value.status_code == 429


# ---------------------------------------------------------------------------
# iter_notes — pagination
# ---------------------------------------------------------------------------

def test_iter_notes_single_page(client):
    page = {"notes": [{"id": "not_1"}, {"id": "not_2"}], "hasMore": False, "cursor": None}
    with patch.object(client, "_get", return_value=page):
        notes = list(client.iter_notes())
    assert [n["id"] for n in notes] == ["not_1", "not_2"]


def test_iter_notes_multiple_pages(client):
    pages = [
        {"notes": [{"id": "not_1"}], "hasMore": True,  "cursor": "cur_abc"},
        {"notes": [{"id": "not_2"}], "hasMore": False, "cursor": None},
    ]
    call_count = {"n": 0}
    def side_effect(path, params=None):
        result = pages[call_count["n"]]
        call_count["n"] += 1
        return result

    with patch.object(client, "_get", side_effect=side_effect):
        notes = list(client.iter_notes())
    assert [n["id"] for n in notes] == ["not_1", "not_2"]
    assert call_count["n"] == 2


def test_iter_notes_infinite_loop_guard(client):
    """hasMore=True with no cursor must NOT loop forever (Bug fix)."""
    call_count = {"n": 0}
    def side_effect(path, params=None):
        call_count["n"] += 1
        if call_count["n"] > 3:
            raise RuntimeError("infinite loop")
        return {"notes": [{"id": "not_1"}], "hasMore": True, "cursor": None}

    with patch.object(client, "_get", side_effect=side_effect):
        notes = list(client.iter_notes())
    assert call_count["n"] == 1          # only one call — safety break triggered
    assert len(notes) == 1


# ---------------------------------------------------------------------------
# list_folders — deduplication
# ---------------------------------------------------------------------------

def test_list_folders_deduplicates(client):
    notes = [
        {"id": "not_1", "folder_membership": [
            {"id": "fol_aaa", "object": "folder", "name": "CS101"},
            {"id": "fol_bbb", "object": "folder", "name": "Algorithms"},
        ]},
        {"id": "not_2", "folder_membership": [
            {"id": "fol_aaa", "object": "folder", "name": "CS101"},  # duplicate
        ]},
    ]
    with patch.object(client, "iter_notes", return_value=iter(notes)):
        folders = client.list_folders()
    assert len(folders) == 2
    ids = {f["id"] for f in folders}
    assert ids == {"fol_aaa", "fol_bbb"}


def test_list_folders_empty_when_no_notes(client):
    with patch.object(client, "iter_notes", return_value=iter([])):
        assert client.list_folders() == []


def test_list_folders_skips_notes_with_no_folders(client):
    notes = [{"id": "not_1", "folder_membership": []}]
    with patch.object(client, "iter_notes", return_value=iter(notes)):
        assert client.list_folders() == []


# ---------------------------------------------------------------------------
# list_notes_in_folder — filtering
# ---------------------------------------------------------------------------

def test_list_notes_in_folder_filters_correctly(client):
    notes = [
        {"id": "not_1", "folder_membership": [{"id": "fol_aaa"}]},
        {"id": "not_2", "folder_membership": [{"id": "fol_bbb"}]},
        {"id": "not_3", "folder_membership": [{"id": "fol_aaa"}, {"id": "fol_bbb"}]},
    ]
    with patch.object(client, "iter_notes", return_value=iter(notes)):
        result = list(client.list_notes_in_folder("fol_aaa"))
    assert [n["id"] for n in result] == ["not_1", "not_3"]


def test_list_notes_in_folder_empty_result(client):
    notes = [{"id": "not_1", "folder_membership": [{"id": "fol_bbb"}]}]
    with patch.object(client, "iter_notes", return_value=iter(notes)):
        result = list(client.list_notes_in_folder("fol_aaa"))
    assert result == []
