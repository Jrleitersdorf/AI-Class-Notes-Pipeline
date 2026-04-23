"""
Sync logic: Granola API → local Markdown files.

Each note is saved as::

    {local_path}/{YYYY-MM-DD} {sanitized_title}.md

File contents::

    # {title}
    Date: {YYYY-MM-DD}
    Attendees: {name1}, {name2}

    ## Notes

    {summary_markdown}

    ---

    ## Transcript

    **[microphone]** text
    **[speaker]** text
    ...

Public entry points
-------------------
``sync_all(client)``         — sync every mapped folder
``sync_folder(folder_id, client)`` — sync one folder
``sync_dry_run(client)``     — preview without writing anything
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Literal

from .granola_client import GranolaClient
from .mappings import get_api_key, list_mappings, _DEFAULT_CONFIG_PATH
from .state import load_state, save_state, is_synced, mark_synced, _DEFAULT_STATE_PATH


# ------------------------------------------------------------------
# Note → Markdown conversion
# ------------------------------------------------------------------

def _sanitize_filename(name: str) -> str:
    """Replace characters not allowed in filenames and strip edge whitespace/dashes."""
    return re.sub(r'[/\\:*?"<>|]', "-", name).strip(" -") or "Untitled"


def _format_transcript(transcript: list[dict] | None) -> str:
    """Convert transcript array to a readable Markdown block."""
    if not transcript:
        return "_No transcript available._"

    lines: list[str] = []
    for item in transcript:
        source = item.get("speaker", {}).get("source", "unknown")
        label = item.get("speaker", {}).get("diarization_label")
        speaker = label if label else f"[{source}]"
        text = item.get("text", "").strip()
        if text:
            lines.append(f"**{speaker}**: {text}")

    return "\n\n".join(lines) if lines else "_No transcript available._"


def note_to_markdown(note: dict) -> str:
    """
    Convert a full Granola Note object (with transcript) to a Markdown string.

    ``note`` must be the result of ``GranolaClient.get_note()`` with
    ``include_transcript=True``.
    """
    title = note.get("title") or "Untitled"
    created_at = note.get("created_at", "")
    date_str = created_at[:10] if created_at else "unknown-date"

    folders = note.get("folder_membership") or []
    folder_names = [f.get("name", "") for f in folders]
    folders_line = ", ".join(filter(None, folder_names)) or "—"

    attendees = note.get("attendees") or []
    attendee_names = [a.get("name") or a.get("email", "") for a in attendees]
    attendees_line = ", ".join(filter(None, attendee_names)) or "—"

    summary_md = (note.get("summary_markdown") or note.get("summary_text") or "").strip()
    summary_section = summary_md if summary_md else "_No notes available._"
    transcript_md = _format_transcript(note.get("transcript"))

    return (
        f"# {title}\n"
        f"Date: {date_str}  \n"
        f"Folders: {folders_line}  \n"
        f"Attendees: {attendees_line}\n"
        f"\n"
        f"## Notes\n"
        f"\n"
        f"{summary_section}\n"
        f"\n"
        f"---\n"
        f"\n"
        f"## Transcript\n"
        f"\n"
        f"{transcript_md}\n"
    )


def _note_filename(note: dict) -> str:
    """Return the local filename (without directory) for a note."""
    created_at = note.get("created_at", "")
    date_str = created_at[:10] if created_at else "0000-00-00"
    title = _sanitize_filename(note.get("title") or "Untitled")
    return f"{date_str} {title}.md"


# ------------------------------------------------------------------
# Result type
# ------------------------------------------------------------------

@dataclass
class NoteResult:
    note_id: str
    title: str
    status: Literal["written", "skipped", "error"]
    file_path: str = ""
    error: str = ""


@dataclass
class FolderSyncResult:
    folder_id: str
    folder_name: str
    local_path: str
    notes: list[NoteResult] = field(default_factory=list)

    @property
    def written(self) -> int:
        return sum(1 for n in self.notes if n.status == "written")

    @property
    def skipped(self) -> int:
        return sum(1 for n in self.notes if n.status == "skipped")

    @property
    def errors(self) -> int:
        return sum(1 for n in self.notes if n.status == "error")


# ------------------------------------------------------------------
# Core sync helpers
# ------------------------------------------------------------------

def _resolve_client(
    client: GranolaClient | None,
    config_path: str,
) -> GranolaClient:
    if client is not None:
        return client
    api_key = get_api_key(config_path=config_path)
    if not api_key:
        # Fall back to environment variable
        api_key = os.environ.get("GRANOLA_API_KEY")
    if not api_key:
        raise ValueError(
            "No Granola API key found. Set it via set_api_key() or the "
            "GRANOLA_API_KEY environment variable."
        )
    return GranolaClient(api_key)


def _sync_one_folder(
    mapping: dict,
    client: GranolaClient,
    state: dict[str, str],
    dry_run: bool,
) -> FolderSyncResult:
    folder_id = mapping["folder_id"]
    folder_name = mapping.get("folder_name", folder_id)
    local_path = mapping["local_path"]

    result = FolderSyncResult(
        folder_id=folder_id,
        folder_name=folder_name,
        local_path=local_path,
    )

    if not dry_run:
        os.makedirs(local_path, exist_ok=True)

    for summary in client.list_notes_in_folder(folder_id):
        note_id = summary["id"]
        updated_at = summary.get("updated_at", "")
        title = summary.get("title") or "Untitled"

        if is_synced(note_id, updated_at, state):
            result.notes.append(
                NoteResult(note_id=note_id, title=title, status="skipped")
            )
            continue

        try:
            if dry_run:
                # In dry-run mode we don't fetch the full note
                file_path = os.path.join(local_path, _note_filename(summary))
                result.notes.append(
                    NoteResult(
                        note_id=note_id,
                        title=title,
                        status="written",
                        file_path=file_path,
                    )
                )
                continue

            full_note = client.get_note(note_id, include_transcript=True)
            markdown = note_to_markdown(full_note)
            filename = _note_filename(full_note)
            file_path = os.path.join(local_path, filename)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown)

            mark_synced(note_id, updated_at, state)
            result.notes.append(
                NoteResult(
                    note_id=note_id,
                    title=title,
                    status="written",
                    file_path=file_path,
                )
            )

        except Exception as exc:
            result.notes.append(
                NoteResult(
                    note_id=note_id,
                    title=title,
                    status="error",
                    error=str(exc),
                )
            )

    return result


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def sync_folder(
    folder_id: str,
    client: GranolaClient | None = None,
    *,
    config_path: str = _DEFAULT_CONFIG_PATH,
    state_path: str = _DEFAULT_STATE_PATH,
) -> FolderSyncResult:
    """
    Sync a single Granola folder to its mapped local directory.

    Returns a :class:`FolderSyncResult` with per-note outcomes.
    Raises ``KeyError`` if ``folder_id`` has no mapping.
    """
    mapping = None
    for m in list_mappings(config_path=config_path):
        if m["folder_id"] == folder_id:
            mapping = m
            break
    if mapping is None:
        raise KeyError(f"No mapping found for folder_id '{folder_id}'.")

    resolved_client = _resolve_client(client, config_path)
    state = load_state(state_path)
    result = _sync_one_folder(mapping, resolved_client, state, dry_run=False)
    save_state(state, state_path)
    return result


def sync_all(
    client: GranolaClient | None = None,
    *,
    config_path: str = _DEFAULT_CONFIG_PATH,
    state_path: str = _DEFAULT_STATE_PATH,
) -> list[FolderSyncResult]:
    """
    Sync all mapped folders.

    Returns one :class:`FolderSyncResult` per mapping.
    """
    mappings = list_mappings(config_path=config_path)
    if not mappings:
        return []

    resolved_client = _resolve_client(client, config_path)
    state = load_state(state_path)
    results: list[FolderSyncResult] = []

    for mapping in mappings:
        result = _sync_one_folder(mapping, resolved_client, state, dry_run=False)
        save_state(state, state_path)  # save after each folder
        results.append(result)

    return results


def sync_dry_run(
    client: GranolaClient | None = None,
    *,
    config_path: str = _DEFAULT_CONFIG_PATH,
    state_path: str = _DEFAULT_STATE_PATH,
) -> list[FolderSyncResult]:
    """
    Preview what *would* be synced without writing any files or updating state.

    Notes that would be written show ``status="written"``; already-synced
    notes show ``status="skipped"``.
    """
    mappings = list_mappings(config_path=config_path)
    if not mappings:
        return []

    resolved_client = _resolve_client(client, config_path)
    state = load_state(state_path)
    results: list[FolderSyncResult] = []

    for mapping in mappings:
        result = _sync_one_folder(mapping, resolved_client, state, dry_run=True)
        results.append(result)

    return results
