"""Tests for src/granola_sync/sync.py"""
import os
from unittest.mock import MagicMock, patch

import pytest

from granola_sync.granola_client import GranolaAPIError
from granola_sync.sync import (
    FolderSyncResult,
    NoteResult,
    _format_transcript,
    _note_filename,
    _sanitize_filename,
    _sync_one_folder,
    note_to_markdown,
)


# ---------------------------------------------------------------------------
# _sanitize_filename
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title,expected", [
    ("Normal Title",          "Normal Title"),
    ("CS101: Recursion",      "CS101- Recursion"),
    (":Leading colon",        "Leading colon"),
    ("Trailing colon:",       "Trailing colon"),
    ("???",                   "Untitled"),       # all-invalid → fallback
    ("",                      "Untitled"),       # empty → fallback
    ("   ",                   "Untitled"),       # spaces only → fallback
    ("Lecture 3/4",           "Lecture 3-4"),
    ("A?B*C",                 "A-B-C"),
])
def test_sanitize_filename(title, expected):
    assert _sanitize_filename(title) == expected


# ---------------------------------------------------------------------------
# _note_filename
# ---------------------------------------------------------------------------

def test_note_filename_normal():
    note = {"title": "Lecture 1", "created_at": "2026-01-10T10:00:00Z"}
    assert _note_filename(note) == "2026-01-10 Lecture 1.md"


def test_note_filename_no_date():
    note = {"title": "Test", "created_at": None}
    assert _note_filename(note) == "0000-00-00 Test.md"


def test_note_filename_no_title():
    note = {"title": None, "created_at": "2026-01-01T00:00:00Z"}
    assert _note_filename(note) == "2026-01-01 Untitled.md"


def test_note_filename_sanitizes_colon():
    note = {"title": "CS101: Recursion", "created_at": "2026-01-10T10:00:00Z"}
    assert _note_filename(note) == "2026-01-10 CS101- Recursion.md"


# ---------------------------------------------------------------------------
# _format_transcript
# ---------------------------------------------------------------------------

def test_format_transcript_none():
    assert _format_transcript(None) == "_No transcript available._"


def test_format_transcript_empty_list():
    assert _format_transcript([]) == "_No transcript available._"


def test_format_transcript_whitespace_only_entries():
    items = [{"speaker": {"source": "microphone"}, "text": "   ",
              "start_time": "2026-01-01T00:00:00Z", "end_time": "2026-01-01T00:01:00Z"}]
    assert _format_transcript(items) == "_No transcript available._"


def test_format_transcript_lecture_strips_labels():
    """Single-microphone lecture: no speaker labels, plain prose."""
    items = [{"speaker": {"source": "microphone"}, "text": "Hello.",
              "start_time": "2026-01-01T00:00:00Z", "end_time": "2026-01-01T00:01:00Z"}]
    result = _format_transcript(items)
    assert "Hello." in result
    assert "[microphone]" not in result
    assert "**" not in result


def test_format_transcript_lecture_merges_fragments():
    """Consecutive lecture utterances within the gap threshold join into one paragraph."""
    items = [
        {"speaker": {"source": "microphone"}, "text": "First sentence.",
         "start_time": "2026-01-01T00:00:00.000Z", "end_time": "2026-01-01T00:00:02.000Z"},
        {"speaker": {"source": "microphone"}, "text": "Second sentence.",
         "start_time": "2026-01-01T00:00:03.000Z", "end_time": "2026-01-01T00:00:05.000Z"},
    ]
    result = _format_transcript(items)
    assert result == "First sentence. Second sentence."


def test_format_transcript_lecture_splits_on_gap():
    """A gap >= 8 s in a lecture creates a new paragraph."""
    items = [
        {"speaker": {"source": "microphone"}, "text": "Topic one.",
         "start_time": "2026-01-01T00:00:00.000Z", "end_time": "2026-01-01T00:00:02.000Z"},
        {"speaker": {"source": "microphone"}, "text": "Topic two.",
         "start_time": "2026-01-01T00:00:12.000Z", "end_time": "2026-01-01T00:00:14.000Z"},
    ]
    result = _format_transcript(items)
    assert result == "Topic one.\n\nTopic two."


def test_format_transcript_conversation_uses_diarization_label():
    """Diarization labels present → conversation mode with labels shown."""
    items = [{"speaker": {"source": "microphone", "diarization_label": "Speaker A"},
              "text": "Hi.", "start_time": "2026-01-01T00:00:00Z", "end_time": "2026-01-01T00:01:00Z"}]
    result = _format_transcript(items)
    assert "**Speaker A**: Hi." in result
    assert "[microphone]" not in result


def test_format_transcript_conversation_merges_same_speaker():
    """Consecutive utterances from the same speaker are joined into one block."""
    items = [
        {"speaker": {"source": "microphone", "diarization_label": "Speaker A"},
         "text": "Hello.", "start_time": "2026-01-01T00:00:00Z", "end_time": "2026-01-01T00:00:01Z"},
        {"speaker": {"source": "microphone", "diarization_label": "Speaker A"},
         "text": "How are you?", "start_time": "2026-01-01T00:00:02Z", "end_time": "2026-01-01T00:00:03Z"},
        {"speaker": {"source": "speaker", "diarization_label": "Speaker B"},
         "text": "Good thanks.", "start_time": "2026-01-01T00:00:04Z", "end_time": "2026-01-01T00:00:05Z"},
    ]
    result = _format_transcript(items)
    assert "**Speaker A**: Hello. How are you?" in result
    assert "**Speaker B**: Good thanks." in result


# ---------------------------------------------------------------------------
# note_to_markdown
# ---------------------------------------------------------------------------

@pytest.fixture
def full_note():
    return {
        "id": "not_abc",
        "title": "CS101: Recursion",
        "created_at": "2026-03-12T14:00:00Z",
        "updated_at": "2026-03-12T15:00:00Z",
        "folder_membership": [
            {"id": "fol_111", "object": "folder", "name": "CS101 Lectures"},
        ],
        "attendees": [
            {"name": "Prof. Smith", "email": "smith@uni.edu"},
            {"name": None, "email": "anon@uni.edu"},
        ],
        "summary_markdown": "## Key Points\n\n- Recursion",
        "transcript": [
            {"speaker": {"source": "microphone"}, "text": "Today: recursion.",
             "start_time": "2026-03-12T14:00:00Z", "end_time": "2026-03-12T14:01:00Z"},
        ],
    }


def test_note_to_markdown_title(full_note):
    md = note_to_markdown(full_note)
    assert md.startswith("# CS101: Recursion\n")


def test_note_to_markdown_date(full_note):
    md = note_to_markdown(full_note)
    assert "Date: 2026-03-12" in md


def test_note_to_markdown_folders(full_note):
    md = note_to_markdown(full_note)
    assert "Folders: CS101 Lectures" in md


def test_note_to_markdown_attendees(full_note):
    md = note_to_markdown(full_note)
    assert "Prof. Smith" in md
    assert "anon@uni.edu" in md   # falls back to email when name is None


def test_note_to_markdown_summary(full_note):
    md = note_to_markdown(full_note)
    assert "## Key Points" in md


def test_note_to_markdown_transcript(full_note):
    md = note_to_markdown(full_note)
    assert "Today: recursion." in md
    assert "## Transcript" in md


def test_note_to_markdown_no_folders(full_note):
    full_note["folder_membership"] = []
    md = note_to_markdown(full_note)
    assert "Folders: —" in md


def test_note_to_markdown_no_attendees(full_note):
    full_note["attendees"] = []
    md = note_to_markdown(full_note)
    assert "Attendees: —" in md


def test_note_to_markdown_null_title(full_note):
    full_note["title"] = None
    md = note_to_markdown(full_note)
    assert md.startswith("# Untitled")


def test_note_to_markdown_null_summary_markdown_falls_back_to_text(full_note):
    full_note["summary_markdown"] = None
    full_note["summary_text"] = "Plain text fallback."
    md = note_to_markdown(full_note)
    assert "Plain text fallback." in md


def test_note_to_markdown_both_summary_null_shows_placeholder(full_note):
    """Bug A fix: null summary must not produce triple blank lines."""
    full_note["summary_markdown"] = None
    full_note["summary_text"] = None
    md = note_to_markdown(full_note)
    assert "_No notes available._" in md
    assert "\n\n\n\n" not in md   # no triple blank line


def test_note_to_markdown_null_transcript(full_note):
    full_note["transcript"] = None
    md = note_to_markdown(full_note)
    assert "_No transcript available._" in md


# ---------------------------------------------------------------------------
# note_to_markdown — extract field (v2.1)
# ---------------------------------------------------------------------------

def test_note_to_markdown_extract_both_default(full_note):
    """Default behaviour is unchanged from V1 — both AI notes and transcript."""
    md = note_to_markdown(full_note)
    assert "## Notes" in md
    assert "## Transcript" in md


def test_note_to_markdown_extract_ai_notes_only(full_note):
    md = note_to_markdown(full_note, extract="ai_notes")
    assert "## Notes" in md
    assert "## Transcript" not in md
    assert "Today: recursion." not in md   # transcript text gone


def test_note_to_markdown_extract_transcript_only(full_note):
    md = note_to_markdown(full_note, extract="transcript")
    assert "## Transcript" in md
    assert "## Notes" not in md
    assert "## Key Points" not in md   # summary headings gone


def test_note_to_markdown_extract_invalid_raises(full_note):
    with pytest.raises(ValueError, match="extract"):
        note_to_markdown(full_note, extract="nonsense")


# ---------------------------------------------------------------------------
# _sync_one_folder — integration-style with mock client
# ---------------------------------------------------------------------------

def _make_notes(n=2):
    return [
        {
            "id": f"not_{chr(97+i)}",
            "title": f"Lecture {i+1}",
            "created_at": f"2026-01-{10+i:02d}T10:00:00Z",
            "updated_at": f"2026-01-{10+i:02d}T11:00:00Z",
            "folder_membership": [{"id": "fol_111", "object": "folder", "name": "CS101"}],
        }
        for i in range(n)
    ]


def _full(summary):
    def _fn(note_id, **kw):
        # Use note_id as part of title so each note gets a unique filename
        return {
            "id": note_id, "title": f"T {note_id}", "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T01:00:00Z",
            "folder_membership": [], "attendees": [],
            "summary_markdown": summary, "transcript": None,
        }
    return _fn


def test_sync_writes_new_notes(tmp_path):
    notes = _make_notes(2)
    client = MagicMock()
    client.list_notes_in_folder.return_value = iter(notes)
    client.get_note.side_effect = _full("Content")

    mapping = {"folder_id": "fol_111", "folder_name": "CS101", "local_path": str(tmp_path)}
    result = _sync_one_folder(mapping, client, {}, dry_run=False)

    assert result.written == 2
    assert result.skipped == 0
    assert result.errors == 0
    assert len(list(tmp_path.iterdir())) == 2


def test_sync_skips_already_synced(tmp_path):
    notes = _make_notes(1)
    state = {notes[0]["id"]: notes[0]["updated_at"]}
    client = MagicMock()
    client.list_notes_in_folder.return_value = iter(notes)

    mapping = {"folder_id": "fol_111", "folder_name": "CS101", "local_path": str(tmp_path)}
    result = _sync_one_folder(mapping, client, state, dry_run=False)

    assert result.skipped == 1
    assert result.written == 0
    assert not client.get_note.called


def test_sync_resyncs_updated_note(tmp_path):
    notes = _make_notes(1)
    state = {notes[0]["id"]: "2000-01-01T00:00:00Z"}  # stale timestamp
    client = MagicMock()
    client.list_notes_in_folder.return_value = iter(notes)
    client.get_note.side_effect = _full("Updated content")

    mapping = {"folder_id": "fol_111", "folder_name": "CS101", "local_path": str(tmp_path)}
    result = _sync_one_folder(mapping, client, state, dry_run=False)

    assert result.written == 1
    assert result.skipped == 0


def test_sync_error_does_not_crash_batch(tmp_path):
    notes = _make_notes(3)
    client = MagicMock()
    client.list_notes_in_folder.return_value = iter(notes)

    def get_note_side_effect(note_id, **kw):
        if note_id == "not_b":
            raise GranolaAPIError(404, "not found")
        return _full("Content")(note_id, **kw)

    client.get_note.side_effect = get_note_side_effect
    state = {}
    mapping = {"folder_id": "fol_111", "folder_name": "CS101", "local_path": str(tmp_path)}
    result = _sync_one_folder(mapping, client, state, dry_run=False)

    assert result.written == 2
    assert result.errors == 1
    assert "not_b" not in state          # error note not persisted to state
    assert "not_a" in state              # good notes ARE persisted


def test_sync_error_note_will_retry(tmp_path):
    """A note that errored must not be in state so it's retried next run."""
    notes = _make_notes(1)
    client = MagicMock()
    client.list_notes_in_folder.return_value = iter(notes)
    client.get_note.side_effect = GranolaAPIError(500, "server error")

    state = {}
    mapping = {"folder_id": "fol_111", "folder_name": "CS101", "local_path": str(tmp_path)}
    _sync_one_folder(mapping, client, state, dry_run=False)

    assert notes[0]["id"] not in state


def test_dry_run_writes_no_files(tmp_path):
    notes = _make_notes(2)
    client = MagicMock()
    client.list_notes_in_folder.return_value = iter(notes)

    mapping = {"folder_id": "fol_111", "folder_name": "CS101", "local_path": str(tmp_path)}
    result = _sync_one_folder(mapping, client, {}, dry_run=True)

    assert result.written == 2          # reported as "would write"
    assert list(tmp_path.iterdir()) == []  # nothing actually written
    assert not client.get_note.called   # no API call in dry run


def test_dry_run_does_not_update_state(tmp_path):
    notes = _make_notes(1)
    client = MagicMock()
    client.list_notes_in_folder.return_value = iter(notes)

    state = {}
    mapping = {"folder_id": "fol_111", "folder_name": "CS101", "local_path": str(tmp_path)}
    _sync_one_folder(mapping, client, state, dry_run=True)

    assert state == {}
