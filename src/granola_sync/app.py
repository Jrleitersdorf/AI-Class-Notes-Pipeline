"""
Granola Sync — PyWebView application & JS↔Python bridge.

Exposes :class:`Api` to JavaScript via ``window.pywebview.api.*``.
Methods are thin wrappers over the existing ``granola_sync`` library —
no business logic lives here.

Launched by ``python -m granola_sync`` (default) or the ``granola-sync``
CLI entry point. The legacy Tkinter GUI is reachable via ``--tkinter``.
"""

from __future__ import annotations

import time
from importlib import metadata
from pathlib import Path

import webview

from . import folder_cache as _folder_cache
from . import mappings as _mappings
from . import state as _state
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
from .progress import SyncProgressRunner
from .sync import sync_all, sync_dry_run, sync_folder


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

    # Created lazily once a window exists
    _runner: SyncProgressRunner | None = None

    def _get_runner(self) -> SyncProgressRunner | None:
        if self._runner is None and webview.windows:
            self._runner = SyncProgressRunner(webview.windows[0])
        return self._runner

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

    # ---------- Sync ----------

    def sync_dry_run(self) -> list[dict]:
        """Return what would be written, without writing anything."""
        results = sync_dry_run(
            config_path=_mappings._DEFAULT_CONFIG_PATH,
            state_path=_state._DEFAULT_STATE_PATH,
        )
        return [
            {
                "folder_id": r.folder_id,
                "folder_name": r.folder_name,
                "local_path": r.local_path,
                "written": r.written,
                "skipped": r.skipped,
                "errors": r.errors,
                "notes": [
                    {"note_id": n.note_id, "title": n.title,
                     "status": n.status, "file_path": n.file_path,
                     "error": n.error}
                    for n in r.notes
                ],
            }
            for r in results
        ]

    def start_sync(self, folder_id: str | None = None) -> str:
        """Kick off a sync in a background thread. See spec for event schema."""
        runner = self._get_runner()
        if runner is None:
            raise RuntimeError("No webview window available.")

        def task(emit, is_cancelled=lambda: False):
            # NOTE: No try/except here — the runner's outer handler in
            # progress.py emits the error event with the correct sync_id.
            # The sync_id fields below are left as "" because the closure
            # cannot know its own sync_id (the runner generates it AFTER
            # runner.start(task)). The frontend treats the value returned
            # by start_sync() as the authoritative sync_id.
            t0 = time.time()
            if folder_id:
                results = sync_folder(
                    folder_id,
                    config_path=_mappings._DEFAULT_CONFIG_PATH,
                    state_path=_state._DEFAULT_STATE_PATH,
                )
            else:
                results = sync_all(
                    config_path=_mappings._DEFAULT_CONFIG_PATH,
                    state_path=_state._DEFAULT_STATE_PATH,
                )
            if isinstance(results, list):
                folder_results = results
            else:
                folder_results = [results]

            written = skipped = errors = 0
            for r in folder_results:
                for note in r.notes:
                    if is_cancelled():
                        return
                    emit({
                        "type": "note",
                        "sync_id": "",
                        "folder_id": r.folder_id,
                        "status": note.status,
                        "note_id": note.note_id,
                        "title": note.title,
                        "file_path": note.file_path,
                        "error": note.error,
                    })
                emit({
                    "type": "folder_done",
                    "sync_id": "",
                    "folder_id": r.folder_id,
                    "folder_name": r.folder_name,
                    "written": r.written,
                    "skipped": r.skipped,
                    "errors": r.errors,
                })
                written += r.written
                skipped += r.skipped
                errors += r.errors

            emit({
                "type": "done",
                "sync_id": "",
                "written": written,
                "skipped": skipped,
                "errors": errors,
                "elapsed_ms": int((time.time() - t0) * 1000),
            })

        return runner.start(task)

    def cancel_sync(self, sync_id: str) -> bool:
        runner = self._get_runner()
        if runner is None:
            return False
        return runner.cancel(sync_id)


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
