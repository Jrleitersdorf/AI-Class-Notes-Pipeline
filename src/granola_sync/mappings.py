"""
CRUD operations for Granola-folder → local-path mappings.

Mappings are persisted as JSON in a config file (default: ``config.json``
in the project root, but callers can point anywhere via ``config_path``).

Config file shape::

    {
      "granola_api_key": "grn_...",
      "mappings": [
        {
          "folder_id":   "fol_4y6LduVdwSKC27",
          "folder_name": "CS101 Lectures",
          "local_path":  "/Users/julian/Notes/CS101"
        }
      ]
    }

All public functions accept an optional ``config_path`` argument. When
omitted the module-level default (``_DEFAULT_CONFIG_PATH``) is used, which
is ``config.json`` in the project root (the directory that contains ``src/``).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# src/granola_sync/ → src/ → project root → config.json
_DEFAULT_CONFIG_PATH = str(Path(__file__).parent.parent.parent / "config.json")

_VALID_EXTRACT = {"both", "ai_notes", "transcript"}


def _normalize_mapping(m: dict) -> dict:
    """Return a mapping dict with all v2.1 fields filled in with defaults."""
    if "extract" not in m or m["extract"] is None:
        m["extract"] = "both"
    return m


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _load(config_path: str) -> dict:
    if not os.path.exists(config_path):
        return {"mappings": []}
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "mappings" not in data:
        data["mappings"] = []
    return data


def _save(data: dict, config_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _find_index(mappings: list[dict], folder_id: str) -> int | None:
    for i, m in enumerate(mappings):
        if m["folder_id"] == folder_id:
            return i
    return None


# ------------------------------------------------------------------
# Public CRUD API
# ------------------------------------------------------------------

def create_mapping(
    folder_id: str,
    folder_name: str,
    local_path: str,
    *,
    extract: str = "both",
    config_path: str = _DEFAULT_CONFIG_PATH,
) -> dict:
    """
    Add a new mapping and return it.

    Raises ``ValueError`` if a mapping for ``folder_id`` already exists,
    or if ``extract`` is not one of ``"both"`` / ``"ai_notes"`` / ``"transcript"``.
    """
    if extract not in _VALID_EXTRACT:
        raise ValueError(
            f"extract must be one of {sorted(_VALID_EXTRACT)}; got {extract!r}"
        )
    data = _load(config_path)
    if _find_index(data["mappings"], folder_id) is not None:
        raise ValueError(
            f"A mapping for folder_id '{folder_id}' already exists. "
            "Use update_mapping() to change it."
        )
    mapping: dict[str, Any] = {
        "folder_id": folder_id,
        "folder_name": folder_name,
        "local_path": str(local_path),
        "extract": extract,
    }
    data["mappings"].append(mapping)
    _save(data, config_path)
    return mapping


def list_mappings(*, config_path: str = _DEFAULT_CONFIG_PATH) -> list[dict]:
    """Return all mappings (may be empty).

    Mappings are normalized at read time so V1 configs (no ``extract``
    field) come back with the default applied. The on-disk file is not
    rewritten — lazy migration happens only when the user explicitly
    saves via ``create_mapping`` / ``update_mapping``.
    """
    data = _load(config_path)
    return [_normalize_mapping(dict(m)) for m in data.get("mappings", [])]


def get_mapping(
    folder_id: str, *, config_path: str = _DEFAULT_CONFIG_PATH
) -> dict | None:
    """Return the mapping for ``folder_id``, or ``None`` if not found."""
    for m in list_mappings(config_path=config_path):
        if m["folder_id"] == folder_id:
            return m
    return None


def update_mapping(
    folder_id: str,
    *,
    folder_name: str | None = None,
    local_path: str | None = None,
    extract: str | None = None,
    config_path: str = _DEFAULT_CONFIG_PATH,
) -> dict:
    """
    Update one or more fields of an existing mapping and return the updated dict.

    Raises ``KeyError`` if no mapping for ``folder_id`` exists, or
    ``ValueError`` if ``extract`` is supplied but not one of the allowed values.
    """
    if extract is not None and extract not in _VALID_EXTRACT:
        raise ValueError(
            f"extract must be one of {sorted(_VALID_EXTRACT)}; got {extract!r}"
        )
    data = _load(config_path)
    idx = _find_index(data["mappings"], folder_id)
    if idx is None:
        raise KeyError(f"No mapping found for folder_id '{folder_id}'.")
    if folder_name is not None:
        data["mappings"][idx]["folder_name"] = folder_name
    if local_path is not None:
        data["mappings"][idx]["local_path"] = str(local_path)
    if extract is not None:
        data["mappings"][idx]["extract"] = extract
    _save(data, config_path)
    return _normalize_mapping(dict(data["mappings"][idx]))


def delete_mapping(
    folder_id: str, *, config_path: str = _DEFAULT_CONFIG_PATH
) -> bool:
    """
    Remove the mapping for ``folder_id``.

    Returns ``True`` if a mapping was removed, ``False`` if it didn't exist.
    """
    data = _load(config_path)
    idx = _find_index(data["mappings"], folder_id)
    if idx is None:
        return False
    data["mappings"].pop(idx)
    _save(data, config_path)
    return True


# ------------------------------------------------------------------
# API key helpers (stored in the same config file)
# ------------------------------------------------------------------

def get_api_key(*, config_path: str = _DEFAULT_CONFIG_PATH) -> str | None:
    """Return the stored Granola API key, or ``None``."""
    return _load(config_path).get("granola_api_key")


def set_api_key(api_key: str, *, config_path: str = _DEFAULT_CONFIG_PATH) -> None:
    """Persist the Granola API key to the config file."""
    data = _load(config_path)
    data["granola_api_key"] = api_key
    _save(data, config_path)
