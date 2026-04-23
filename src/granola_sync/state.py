"""
Sync state tracker.

Persists a mapping of ``note_id → updated_at`` (ISO-8601 string) in a
``.state.json`` file so the sync loop can skip notes that haven't changed.

The state file lives alongside ``config.json`` in the project root by default,
but callers can supply any path.

If a note's upload/write fails the caller should simply not call
``mark_synced()``, which means the note will be retried on the next run.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# src/granola_sync/ → src/ → project root → .state.json
_DEFAULT_STATE_PATH = str(Path(__file__).parent.parent.parent / ".state.json")


def load_state(state_path: str = _DEFAULT_STATE_PATH) -> dict[str, str]:
    """Load and return the persisted state dict (note_id → updated_at)."""
    if not os.path.exists(state_path):
        return {}
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(
    state: dict[str, str], state_path: str = _DEFAULT_STATE_PATH
) -> None:
    """Persist the state dict to disk."""
    os.makedirs(os.path.dirname(os.path.abspath(state_path)), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def is_synced(
    note_id: str, updated_at: str, state: dict[str, str]
) -> bool:
    """Return True if the note is already up-to-date in the local store."""
    return state.get(note_id) == updated_at


def mark_synced(
    note_id: str, updated_at: str, state: dict[str, str]
) -> None:
    """
    Record that a note has been successfully synced.

    Mutates ``state`` in-place; the caller is responsible for persisting it
    with :func:`save_state` (typically after each successful write so a
    crash mid-batch doesn't lose all progress).
    """
    state[note_id] = updated_at
