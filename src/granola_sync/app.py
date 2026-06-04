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
    get_api_key,
    set_api_key,
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
