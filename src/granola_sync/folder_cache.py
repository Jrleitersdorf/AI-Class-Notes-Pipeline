"""
Persistent cache of discovered Granola folders.

The Granola API has no folder-listing endpoint; `GranolaClient.list_folders()`
discovers folders by paginating every note and reading each note's
`folder_membership` array (see [TD-001](../../docs/tech-debt.md) — O(N) API
calls). For users with hundreds of notes that's ~40 s at the rate limit.

This module persists the result to ``.folders.json`` at the project root so
the GUI (and any library consumer) can show folders **instantly** on startup
and only re-fetch from the API when the user explicitly asks.

Cache file layout::

    {
      "folders": [
        {"id": "fol_xxx", "object": "folder", "name": "CS101"},
        ...
      ],
      "refreshed_at": "2026-04-24T15:30:00+00:00"
    }

The cache is **hand-refreshed only** (no TTL). The GUI exposes a "Refresh
Folders" button that calls :func:`refresh_folder_cache` to re-fetch from the
API and overwrite the cache.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .granola_client import GranolaClient

# src/granola_sync/ → src/ → project root → .folders.json
_DEFAULT_CACHE_PATH = str(Path(__file__).parent.parent.parent / ".folders.json")


def load_folder_cache(cache_path: str = _DEFAULT_CACHE_PATH) -> dict:
    """
    Load the cached folder list.

    Returns a dict with two keys:

    - ``folders`` (list[dict]) — folder objects as returned by
      :meth:`GranolaClient.list_folders`. Empty list when no cache exists yet.
    - ``refreshed_at`` (str | None) — ISO-8601 timestamp of when the cache
      was last refreshed. ``None`` when no cache exists yet.

    A missing or unreadable cache file produces an empty result rather than
    an exception — the GUI treats that as "show nothing, prompt the user to
    click Refresh".
    """
    if not os.path.exists(cache_path):
        return {"folders": [], "refreshed_at": None}
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupted cache — degrade gracefully; user can Refresh to rebuild.
        return {"folders": [], "refreshed_at": None}
    folders = data.get("folders") or []
    refreshed_at = data.get("refreshed_at")
    return {"folders": folders, "refreshed_at": refreshed_at}


def save_folder_cache(
    folders: list[dict],
    cache_path: str = _DEFAULT_CACHE_PATH,
) -> str:
    """
    Persist a folder list to disk, stamped with the current UTC time.

    Returns the ``refreshed_at`` timestamp that was written so callers can
    display it without re-reading the file.
    """
    refreshed_at = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)
    payload = {"folders": list(folders), "refreshed_at": refreshed_at}
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    return refreshed_at


def refresh_folder_cache(
    client: GranolaClient,
    cache_path: str = _DEFAULT_CACHE_PATH,
) -> dict:
    """
    Fetch the folder list from the API, persist it, and return the new cache.

    Equivalent shape to :func:`load_folder_cache`. Use this when the user
    clicks "Refresh" in the GUI or wants a fresh discovery from the CLI.
    """
    folders = client.list_folders()
    refreshed_at = save_folder_cache(folders, cache_path=cache_path)
    return {"folders": folders, "refreshed_at": refreshed_at}
