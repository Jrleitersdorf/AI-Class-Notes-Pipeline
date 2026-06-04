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


_PACKAGE_NAME = "granola_sync"


def _find_frontend_index() -> Path | None:
    """Locate index.html, trying the in-package copy first (wheel install)
    then the repo's frontend/dist/ (editable install)."""
    here = Path(__file__).resolve().parent
    candidates = [
        here / "_frontend" / "index.html",                                # wheel install
        here.parent.parent.parent / "frontend" / "dist" / "index.html",   # editable dev install
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
