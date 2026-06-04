"""
Granola Sync — PyWebView application & JS↔Python bridge.

Exposes :class:`Api` to JavaScript via ``window.pywebview.api.*``.
Methods are thin wrappers over the existing ``granola_sync`` library —
no business logic lives here.

Launched by ``python -m granola_sync`` (default) or the ``granola-sync``
CLI entry point. The legacy Tkinter GUI is reachable via ``--tkinter``.
"""

from __future__ import annotations

from importlib import metadata
from pathlib import Path

import webview

from . import folder_cache as _folder_cache
from . import mappings as _mappings
from .folder_cache import load_folder_cache, refresh_folder_cache
from .granola_client import GranolaClient
from .mappings import (
    create_mapping,
    delete_mapping,
    get_api_key,
    list_mappings,
    set_api_key,
    update_mapping,
)


_PACKAGE_NAME = "granola_sync"


def _find_frontend_index() -> Path | None:
    """Locate index.html, trying the in-package copy first (wheel install)
    then the repo's frontend/dist/ (editable install)."""
    here = Path(__file__).resolve().parent
    candidates = [
        here / "_frontend" / "index.html",                                # wheel install
        here.parent.parent / "frontend" / "dist" / "index.html",          # editable dev install
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


class Api:
    """JS-callable bridge surface."""

    # ---------- App control ----------

    def get_version(self) -> str:
        """Return the installed package version (x.y.z)."""
        try:
            return metadata.version(_PACKAGE_NAME)
        except metadata.PackageNotFoundError:
            return "0.0.0+unknown"

    # ---------- API key ----------

    def get_api_key(self) -> str | None:
        return get_api_key(config_path=_mappings._DEFAULT_CONFIG_PATH)

    def set_api_key(self, key: str) -> None:
        set_api_key(key.strip(), config_path=_mappings._DEFAULT_CONFIG_PATH)

    # ---------- Folder cache ----------

    def load_cached_folders(self) -> dict:
        return load_folder_cache(cache_path=_folder_cache._DEFAULT_CACHE_PATH)

    def refresh_folders(self) -> dict:
        key = get_api_key(config_path=_mappings._DEFAULT_CONFIG_PATH)
        if not key:
            raise RuntimeError("No API key configured.")
        client = GranolaClient(key)
        return refresh_folder_cache(
            client, cache_path=_folder_cache._DEFAULT_CACHE_PATH
        )

    # ---------- Mappings ----------

    def list_mappings(self) -> list[dict]:
        return list_mappings(config_path=_mappings._DEFAULT_CONFIG_PATH)

    def create_mapping(
        self,
        folder_id: str,
        folder_name: str,
        local_path: str,
        extract: str = "both",
    ) -> dict:
        return create_mapping(
            folder_id,
            folder_name,
            local_path,
            extract=extract,
            config_path=_mappings._DEFAULT_CONFIG_PATH,
        )

    def update_mapping(self, folder_id: str, **fields) -> dict:
        return update_mapping(
            folder_id,
            config_path=_mappings._DEFAULT_CONFIG_PATH,
            **fields,
        )

    def delete_mapping(self, folder_id: str) -> bool:
        return delete_mapping(
            folder_id,
            config_path=_mappings._DEFAULT_CONFIG_PATH,
        )

    # ---------- OS folder picker ----------

    def pick_folder(self, title: str = "Choose folder") -> str | None:
        """Open the native folder picker. Returns the chosen path or None."""
        if not webview.windows:
            return None
        result = webview.windows[0].create_file_dialog(
            webview.FOLDER_DIALOG,
            allow_multiple=False,
        )
        if not result:
            return None
        # create_file_dialog returns a tuple of strings
        return result[0] if isinstance(result, (list, tuple)) else result


def launch(*, dev_url: str | None = None) -> None:
    """
    Spawn the pywebview window.

    Parameters
    ----------
    dev_url
        If set, the webview loads from this URL (Vite dev server).
        Otherwise it loads ``frontend/dist/index.html`` bundled with the package.
    """
    api = Api()

    if dev_url:
        url = dev_url
    else:
        index = _find_frontend_index()
        if index is None:
            raise FileNotFoundError(
                "Frontend not built. Run `make build`, or `cd frontend && "
                "npm install && npm run build`, or use `--tkinter` to "
                "launch the V1 GUI."
            )
        url = index.as_uri()

    webview.create_window(
        title="Granola Sync",
        url=url,
        js_api=api,
        width=900,
        height=640,
        min_size=(720, 520),
    )
    webview.start()
