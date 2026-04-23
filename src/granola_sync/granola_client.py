"""
Granola public API client.

Wraps GET /v1/notes (paginated) and GET /v1/notes/{id}?include=transcript.
Auth: Authorization: Bearer <api_key>
"""

from __future__ import annotations

import time
from typing import Iterator

import requests

BASE_URL = "https://public-api.granola.ai"
_DEFAULT_PAGE_SIZE = 30  # max allowed by the API


class GranolaAPIError(Exception):
    """Raised when the Granola API returns an error response."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Granola API error {status_code}: {message}")


class GranolaClient:
    """
    Client for the Granola public API.

    Usage::

        client = GranolaClient(api_key="grn_...")
        for folder in client.list_folders():
            print(folder["id"], folder["name"])

        for note in client.list_notes_in_folder("fol_xxx"):
            full = client.get_note(note["id"])
            print(full["summary_markdown"])
    """

    def __init__(self, api_key: str):
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {api_key}"})

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = BASE_URL + path
        resp = self._session.get(url, params=params or {})
        if resp.status_code == 429:
            # Simple back-off: wait 1 s then retry once
            time.sleep(1)
            resp = self._session.get(url, params=params or {})
        if not resp.ok:
            raise GranolaAPIError(resp.status_code, resp.text[:200])
        return resp.json()

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------

    def iter_notes(
        self,
        *,
        created_after: str | None = None,
        created_before: str | None = None,
        updated_after: str | None = None,
    ) -> Iterator[dict]:
        """
        Yield every NoteSummary object, handling pagination automatically.

        Parameters are ISO-8601 date strings (e.g. ``"2026-01-01"`` or
        ``"2026-01-01T00:00:00Z"``).
        """
        params: dict = {"page_size": _DEFAULT_PAGE_SIZE}
        if created_after:
            params["created_after"] = created_after
        if created_before:
            params["created_before"] = created_before
        if updated_after:
            params["updated_after"] = updated_after

        cursor: str | None = None
        while True:
            if cursor:
                params["cursor"] = cursor
            data = self._get("/v1/notes", params)
            for note in data.get("notes", []):
                yield note
            if not data.get("hasMore"):
                break
            cursor = data.get("cursor")

    def get_note(self, note_id: str, *, include_transcript: bool = True) -> dict:
        """
        Fetch a full Note object by ID.

        Pass ``include_transcript=True`` (the default) to include the
        ``transcript`` array in the response.
        """
        params = {}
        if include_transcript:
            params["include"] = "transcript"
        return self._get(f"/v1/notes/{note_id}", params)

    # ------------------------------------------------------------------
    # Folders
    # ------------------------------------------------------------------

    def list_folders(self) -> list[dict]:
        """
        Return a deduplicated list of all Folder objects visible to this key.

        Folders are discovered by iterating every note and collecting unique
        ``folder_membership`` entries — the API has no dedicated folder list
        endpoint.

        Each folder dict has keys: ``id``, ``object``, ``name``.
        """
        seen: dict[str, dict] = {}
        for note in self.iter_notes():
            for folder in note.get("folder_membership", []):
                if folder["id"] not in seen:
                    seen[folder["id"]] = folder
        return list(seen.values())

    def list_notes_in_folder(
        self,
        folder_id: str,
        *,
        updated_after: str | None = None,
    ) -> Iterator[dict]:
        """
        Yield NoteSummary objects that belong to ``folder_id``.

        Optionally pass ``updated_after`` (ISO-8601) to restrict to recently
        changed notes.
        """
        for note in self.iter_notes(updated_after=updated_after):
            memberships = [f["id"] for f in note.get("folder_membership", [])]
            if folder_id in memberships:
                yield note
