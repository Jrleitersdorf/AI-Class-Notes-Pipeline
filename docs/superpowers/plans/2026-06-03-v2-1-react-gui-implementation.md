# V2.1 — React GUI scaffold + first-launch wizard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship feature parity with the V1 Tkinter GUI inside a new PyWebView + React frontend, plus a first-launch wizard that gets a fresh non-developer user from "downloaded" to "first sync complete" in under 2 minutes.

**Architecture:** Single Python process hosts a pywebview window. React + TypeScript + Vite + Tailwind + shadcn/ui frontend in `frontend/`. Python `Api` class in `src/granola_sync/app.py` is exposed to JavaScript via the pywebview JS↔Python bridge. The V1 `granola_sync` library is unchanged and remains the source of truth — the bridge is a thin wrapper. Sync progress is streamed from a background Python thread via `window.evaluate_js`.

**Tech Stack:** Python 3.10+ (pywebview, pyobjc-core, pyobjc-framework-WebKit), Node 20+ (Vite, React 19, TypeScript, Tailwind 3, shadcn/ui, Zustand, Vitest, Playwright). Spec: `docs/superpowers/specs/2026-06-03-v2-1-react-gui-design.md`.

**Branch:** start on a new branch off `main` named `feat/v2-1-react-gui`. Do **not** merge into `main` until Phase 8's final commit; intermediate phases land as a single PR at the end.

---

## File structure

### Created

| Path | Responsibility |
|---|---|
| `src/granola_sync/app.py` | `Api` class exposed to JS; spawns pywebview window. No business logic — every method delegates to the library. |
| `src/granola_sync/progress.py` | Threaded sync runner that emits structured progress events via `window.evaluate_js`. |
| `tests/test_app.py` | Bridge tests with a mocked `webview.Window`. |
| `tests/test_progress.py` | Progress helper tests. |
| `frontend/package.json` | Node deps + scripts. |
| `frontend/vite.config.ts` | Vite config (relative base path so it works in `file://`). |
| `frontend/tsconfig.json` | TypeScript config. |
| `frontend/tailwind.config.js` | Tailwind v3 config consuming the theme tokens. |
| `frontend/postcss.config.js` | PostCSS for Tailwind. |
| `frontend/index.html` | Vite entry HTML. |
| `frontend/src/main.tsx` | React mount + ErrorBoundary. |
| `frontend/src/App.tsx` | Top-level router (wizard vs tabs). |
| `frontend/src/api.ts` | Typed wrapper around `window.pywebview.api.*` + `SyncEvent` types. |
| `frontend/src/theme.css` | CSS variables: colors, fonts, radii. |
| `frontend/src/state/index.ts` | Zustand store assembly. |
| `frontend/src/state/setup.ts` | Setup slice (api key, folders, refreshed_at). |
| `frontend/src/state/mappings.ts` | Mappings slice. |
| `frontend/src/state/sync.ts` | Sync slice (sync_id, progress events, running flag). |
| `frontend/src/state/ui.ts` | UI slice (current tab, wizard step, toasts). |
| `frontend/src/screens/Wizard/index.tsx` | Wizard shell + 4-step router. |
| `frontend/src/screens/Wizard/Step1ApiKey.tsx` | API key entry. |
| `frontend/src/screens/Wizard/Step2Folders.tsx` | Folder discovery + selection. |
| `frontend/src/screens/Wizard/Step3Mapping.tsx` | First mapping via drop / pick. |
| `frontend/src/screens/Wizard/Step4Done.tsx` | Success + "Sync now?". |
| `frontend/src/screens/Setup/index.tsx` | Setup tab (API key card + folders card). |
| `frontend/src/screens/Mappings/index.tsx` | Mappings tab side-by-side layout. |
| `frontend/src/screens/Mappings/NewMappingDialog.tsx` | "+ New mapping" stub for drag-drop. |
| `frontend/src/screens/Mappings/ConfigPopover.tsx` | Per-mapping ⚙ popover (extract config + delete). |
| `frontend/src/screens/Sync/index.tsx` | Sync tab buttons + log. |
| `frontend/src/components/Button.tsx` | shadcn-style button. |
| `frontend/src/components/Card.tsx` | Card wrapper. |
| `frontend/src/components/Input.tsx` | Text input (masked / unmasked). |
| `frontend/src/components/Tabs.tsx` | Tab strip + tab content. |
| `frontend/src/components/EmptyState.tsx` | Icon + title + body + CTA. |
| `frontend/src/components/Toast.tsx` | Bottom-right toast for errors. |
| `frontend/src/components/ErrorBoundary.tsx` | Top-level React error boundary. |
| `frontend/src/lib/cn.ts` | `cn()` className helper (clsx + tailwind-merge). |
| `frontend/src/lib/format.ts` | `formatRelativeTime`. |
| `frontend/src/__tests__/*` (multiple) | Vitest + RTL tests, mirroring component locations. |
| `frontend/playwright.config.ts` | Playwright config. |
| `frontend/tests/e2e/wizard.spec.ts` | Wizard happy-path E2E. |
| `Makefile` | `make dev`, `make build`, `make test`. |
| `.github/workflows/ci.yml` | macOS + Ubuntu × Python 3.10/3.12 × Node 20. |

### Modified

| Path | Change |
|---|---|
| `src/granola_sync/__main__.py` | Launch pywebview by default; `--tkinter` flag falls back to V1 GUI. |
| `src/granola_sync/__init__.py` | Re-export `Api` from `app.py`. |
| `src/granola_sync/mappings.py` | Add `extract` field to mapping records (default `"both"`). |
| `src/granola_sync/sync.py` | `note_to_markdown` respects the mapping's `extract` field. |
| `tests/test_mappings.py` | Tests for the `extract` field round-trip. |
| `tests/test_sync.py` | Tests for extract-aware `note_to_markdown`. |
| `pyproject.toml` | Add `pywebview`, `pyobjc-core`, `pyobjc-framework-WebKit` deps. Add `package-data` for `frontend/dist/**`. |
| `requirements.txt` | Add `pywebview>=5.0`. |
| `CLAUDE.md` | Document `app.py` and the bridge layer. |
| `CHANGELOG.md` | New `[2.1.0]` section. |
| `docs/versions/v2.md` | Mark v2.1 IN PROGRESS → SHIPPED at Phase 8. |

---

# Phase 1 · Library prep (extract field)

Backend-only changes that the new GUI will consume. No frontend touched. End of phase: all 85 V1 tests still pass plus 6+ new ones for the `extract` field.

## Task 1 · Add `extract` field to mapping records

**Files:**
- Modify: `src/granola_sync/mappings.py`
- Modify: `tests/test_mappings.py`

The field accepts one of: `"both"` | `"ai_notes"` | `"transcript"`. Default: `"both"` for backward compat with V1 configs that have no field.

- [ ] **Step 1.1: Write the failing test for `extract` default**

Append to `tests/test_mappings.py`:

```python
# ---------------------------------------------------------------------------
# extract field (v2.1)
# ---------------------------------------------------------------------------

def test_create_mapping_defaults_extract_to_both(cfg):
    m = create_mapping("fol_aaa", "CS101", "/tmp/notes", config_path=cfg)
    assert m["extract"] == "both"


def test_create_mapping_accepts_explicit_extract(cfg):
    m = create_mapping("fol_aaa", "CS101", "/tmp/notes",
                       extract="ai_notes", config_path=cfg)
    assert m["extract"] == "ai_notes"


def test_create_mapping_rejects_invalid_extract(cfg):
    with pytest.raises(ValueError, match="extract"):
        create_mapping("fol_aaa", "CS101", "/tmp/notes",
                       extract="bogus", config_path=cfg)


def test_update_mapping_can_change_extract(cfg):
    create_mapping("fol_aaa", "CS101", "/tmp/a", config_path=cfg)
    updated = update_mapping("fol_aaa", extract="transcript", config_path=cfg)
    assert updated["extract"] == "transcript"


def test_load_pre_v2_mapping_defaults_extract(cfg):
    """Mappings written by V1 (no extract field) must load as 'both'."""
    import json
    with open(cfg, "w") as f:
        json.dump({
            "mappings": [
                {"folder_id": "fol_old", "folder_name": "Old", "local_path": "/tmp/x"}
            ]
        }, f)
    m = get_mapping("fol_old", config_path=cfg)
    assert m["extract"] == "both"


def test_update_mapping_rejects_invalid_extract(cfg):
    create_mapping("fol_aaa", "CS101", "/tmp/a", config_path=cfg)
    with pytest.raises(ValueError, match="extract"):
        update_mapping("fol_aaa", extract="nope", config_path=cfg)
```

- [ ] **Step 1.2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_mappings.py -v -k "extract or pre_v2" 2>&1 | tail -20`
Expected: 6 failures with `TypeError: create_mapping() got an unexpected keyword argument 'extract'` or similar.

- [ ] **Step 1.3: Implement the `extract` field in `mappings.py`**

In `src/granola_sync/mappings.py`, near the top (after imports), add the allowed-values constant:

```python
_VALID_EXTRACT = {"both", "ai_notes", "transcript"}


def _normalize_mapping(m: dict) -> dict:
    """Return a mapping dict with all v2.1 fields filled in with defaults."""
    if "extract" not in m or m["extract"] is None:
        m["extract"] = "both"
    return m
```

Modify `create_mapping` to accept and validate `extract`:

```python
def create_mapping(
    folder_id: str,
    folder_name: str,
    local_path: str,
    *,
    extract: str = "both",
    config_path: str = _DEFAULT_CONFIG_PATH,
) -> dict:
    if extract not in _VALID_EXTRACT:
        raise ValueError(
            f"extract must be one of {sorted(_VALID_EXTRACT)}; got {extract!r}"
        )
    # … existing duplicate-check logic …
    mapping = {
        "folder_id": folder_id,
        "folder_name": folder_name,
        "local_path": local_path,
        "extract": extract,
    }
    # … existing write logic …
```

Modify `update_mapping` to validate `extract` if supplied:

```python
def update_mapping(folder_id: str, *, config_path: str = _DEFAULT_CONFIG_PATH, **fields) -> dict:
    if "extract" in fields and fields["extract"] not in _VALID_EXTRACT:
        raise ValueError(
            f"extract must be one of {sorted(_VALID_EXTRACT)}; got {fields['extract']!r}"
        )
    # … existing logic …
```

Apply `_normalize_mapping` in both `list_mappings` and `get_mapping` (read-side) so old configs auto-default:

```python
def list_mappings(*, config_path: str = _DEFAULT_CONFIG_PATH) -> list[dict]:
    data = _read(config_path)
    return [_normalize_mapping(dict(m)) for m in data.get("mappings", [])]


def get_mapping(folder_id: str, *, config_path: str = _DEFAULT_CONFIG_PATH) -> dict | None:
    for m in list_mappings(config_path=config_path):
        if m["folder_id"] == folder_id:
            return m
    return None
```

Note: `_normalize_mapping` mutates the dict copy returned by `list_mappings`, not the on-disk file. We never auto-rewrite the user's `config.json` (lazy migration — open-question #1 in the spec).

- [ ] **Step 1.4: Run tests to verify they pass**

Run: `python3 -m pytest tests/ -v 2>&1 | tail -5`
Expected: 91 passed (85 existing + 6 new).

- [ ] **Step 1.5: Commit**

```bash
git add src/granola_sync/mappings.py tests/test_mappings.py
git commit -m "$(cat <<'EOF'
feat(mappings): add `extract` field for V2.1 per-mapping config

Each mapping now carries an `extract` field — one of "both" |
"ai_notes" | "transcript", default "both". Validated at create_mapping
and update_mapping. V1 mappings without the field load with the
default applied at read time (lazy migration; the on-disk config is
never rewritten without an explicit save).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

## Task 2 · `note_to_markdown` respects `extract`

**Files:**
- Modify: `src/granola_sync/sync.py`
- Modify: `tests/test_sync.py`

The V1 `note_to_markdown(note)` signature must stay backward-compatible (defaulting to "both"). Add an optional `extract` parameter.

- [ ] **Step 2.1: Write the failing tests**

Append to `tests/test_sync.py`:

```python
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
```

- [ ] **Step 2.2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_sync.py -v -k "extract" 2>&1 | tail -10`
Expected: 4 failures with `TypeError: note_to_markdown() got an unexpected keyword argument 'extract'`.

- [ ] **Step 2.3: Implement `extract` parameter**

In `src/granola_sync/sync.py`, modify `note_to_markdown`:

```python
_VALID_EXTRACT = {"both", "ai_notes", "transcript"}


def note_to_markdown(note: dict, *, extract: str = "both") -> str:
    """
    Convert a full Granola Note object to a Markdown string.

    ``extract`` controls which sections appear:
    - ``"both"`` (default) — title + metadata + AI summary + transcript
    - ``"ai_notes"`` — title + metadata + AI summary only
    - ``"transcript"`` — title + metadata + transcript only
    """
    if extract not in _VALID_EXTRACT:
        raise ValueError(
            f"extract must be one of {sorted(_VALID_EXTRACT)}; got {extract!r}"
        )

    title = note.get("title") or "Untitled"
    created_at = note.get("created_at", "")
    date_str = created_at[:10] if created_at else "unknown-date"

    folders = note.get("folder_membership") or []
    folder_names = [f.get("name", "") for f in folders]
    folders_line = ", ".join(filter(None, folder_names)) or "—"

    attendees = note.get("attendees") or []
    attendee_names = [a.get("name") or a.get("email", "") for a in attendees]
    attendees_line = ", ".join(filter(None, attendee_names)) or "—"

    header = (
        f"# {title}\n"
        f"Date: {date_str}  \n"
        f"Folders: {folders_line}  \n"
        f"Attendees: {attendees_line}\n"
    )

    parts = [header]

    if extract in ("both", "ai_notes"):
        summary_md = (note.get("summary_markdown") or note.get("summary_text") or "").strip()
        summary_section = summary_md if summary_md else "_No notes available._"
        parts.append(f"\n## Notes\n\n{summary_section}\n")

    if extract == "both":
        parts.append("\n---\n")

    if extract in ("both", "transcript"):
        transcript_md = _format_transcript(note.get("transcript"))
        parts.append(f"\n## Transcript\n\n{transcript_md}\n")

    return "".join(parts)
```

Then update `_sync_one_folder` to pass the mapping's `extract` field through:

```python
def _sync_one_folder(
    mapping: dict,
    client: GranolaClient,
    state: dict[str, str],
    dry_run: bool,
) -> FolderSyncResult:
    folder_id = mapping["folder_id"]
    folder_name = mapping.get("folder_name", folder_id)
    local_path = mapping["local_path"]
    extract = mapping.get("extract", "both")
    # … existing loop, but the markdown call becomes …
    markdown = note_to_markdown(full_note, extract=extract)
    # … rest unchanged …
```

- [ ] **Step 2.4: Run tests to verify they pass**

Run: `python3 -m pytest tests/ -v 2>&1 | tail -5`
Expected: 95 passed (91 + 4 new).

- [ ] **Step 2.5: Commit**

```bash
git add src/granola_sync/sync.py tests/test_sync.py
git commit -m "$(cat <<'EOF'
feat(sync): note_to_markdown respects per-mapping extract field

Optional `extract` kwarg on note_to_markdown; "both" (default) keeps
v1.1 behaviour, "ai_notes" omits the transcript section, "transcript"
omits the notes section. _sync_one_folder passes the mapping's
extract field through. v1.x callers without the kwarg are unaffected.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

# Phase 2 · Python bridge layer

Lay down `app.py` and `progress.py` with the `Api` class skeleton and the threaded sync runner. No frontend yet — bridge methods are exercised via mocked-webview unit tests.

## Task 3 · Add pywebview dependency

**Files:**
- Modify: `pyproject.toml`
- Modify: `requirements.txt`

- [ ] **Step 3.1: Add the dependency**

In `pyproject.toml`, locate the `dependencies` list and append:

```toml
[project]
# … existing keys …
dependencies = [
  "requests>=2.31.0",
  "pywebview>=5.0",
  # macOS WebKit backend for pywebview:
  "pyobjc-core>=10.0 ; sys_platform == 'darwin'",
  "pyobjc-framework-WebKit>=10.0 ; sys_platform == 'darwin'",
]
```

In `requirements.txt`, append:

```
pywebview>=5.0
pyobjc-core>=10.0 ; sys_platform == 'darwin'
pyobjc-framework-WebKit>=10.0 ; sys_platform == 'darwin'
```

- [ ] **Step 3.2: Install and verify import**

Run:
```bash
pip install -e . -q && python3 -c "import webview; print(webview.__version__)"
```
Expected: prints a version number (5.x or higher).

- [ ] **Step 3.3: Commit**

```bash
git add pyproject.toml requirements.txt
git commit -m "build(deps): add pywebview + macOS pyobjc backends"
```

## Task 4 · `app.py` skeleton + `get_version` bridge method

**Files:**
- Create: `src/granola_sync/app.py`
- Create: `tests/test_app.py`

- [ ] **Step 4.1: Write the failing test**

Create `tests/test_app.py`:

```python
"""Tests for src/granola_sync/app.py — the JS↔Python bridge."""
from unittest.mock import MagicMock, patch

import pytest

from granola_sync.app import Api


@pytest.fixture
def api():
    return Api()


# ---------------------------------------------------------------------------
# get_version
# ---------------------------------------------------------------------------

def test_get_version_returns_string(api):
    v = api.get_version()
    assert isinstance(v, str) and len(v) > 0
    assert v.count(".") >= 2          # x.y.z
```

- [ ] **Step 4.2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_app.py -v 2>&1 | tail -5`
Expected: `ModuleNotFoundError: No module named 'granola_sync.app'`.

- [ ] **Step 4.3: Create the `Api` class skeleton**

Create `src/granola_sync/app.py`:

```python
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
```

- [ ] **Step 4.4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_app.py -v 2>&1 | tail -5`
Expected: 1 passed.

- [ ] **Step 4.5: Commit**

```bash
git add src/granola_sync/app.py tests/test_app.py
git commit -m "feat(app): scaffold Api class + pywebview launcher"
```

## Task 5 · Setup-related bridge methods

**Files:**
- Modify: `src/granola_sync/app.py`
- Modify: `tests/test_app.py`

Add `get_api_key`, `set_api_key`, `load_cached_folders`, `refresh_folders`.

- [ ] **Step 5.1: Write the failing tests**

Append to `tests/test_app.py`:

```python
# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------

def test_set_and_get_api_key_roundtrip(api, tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH", str(cfg))
    assert api.get_api_key() is None
    api.set_api_key("grn_testkey")
    assert api.get_api_key() == "grn_testkey"


# ---------------------------------------------------------------------------
# Folder cache
# ---------------------------------------------------------------------------

def test_load_cached_folders_empty_when_missing(api, tmp_path, monkeypatch):
    monkeypatch.setattr("granola_sync.folder_cache._DEFAULT_CACHE_PATH",
                        str(tmp_path / ".folders.json"))
    result = api.load_cached_folders()
    assert result == {"folders": [], "refreshed_at": None}


def test_refresh_folders_calls_client_and_saves(api, tmp_path, monkeypatch):
    cache = tmp_path / ".folders.json"
    monkeypatch.setattr("granola_sync.folder_cache._DEFAULT_CACHE_PATH", str(cache))
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH",
                        str(tmp_path / "config.json"))
    api.set_api_key("grn_testkey")

    folders = [{"id": "fol_x", "object": "folder", "name": "CS101"}]
    with patch("granola_sync.app.GranolaClient") as ClientCls:
        ClientCls.return_value.list_folders.return_value = folders
        result = api.refresh_folders()

    assert result["folders"] == folders
    assert result["refreshed_at"] is not None


def test_refresh_folders_no_api_key_raises(api, tmp_path, monkeypatch):
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH",
                        str(tmp_path / "config.json"))
    with pytest.raises(RuntimeError, match="No API key"):
        api.refresh_folders()
```

- [ ] **Step 5.2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_app.py -v 2>&1 | tail -10`
Expected: 4 failures (`AttributeError: 'Api' object has no attribute …`).

- [ ] **Step 5.3: Implement the setup methods**

In `src/granola_sync/app.py`, add imports near the top:

```python
from .folder_cache import load_folder_cache, refresh_folder_cache
from .granola_client import GranolaClient
from .mappings import (
    create_mapping,
    delete_mapping,
    get_api_key,
    get_mapping,
    list_mappings,
    set_api_key,
    update_mapping,
)
```

Then add to the `Api` class:

```python
    # ---------- API key ----------

    def get_api_key(self) -> str | None:
        return get_api_key()

    def set_api_key(self, key: str) -> None:
        set_api_key(key.strip())

    # ---------- Folder cache ----------

    def load_cached_folders(self) -> dict:
        return load_folder_cache()

    def refresh_folders(self) -> dict:
        key = get_api_key()
        if not key:
            raise RuntimeError("No API key configured.")
        client = GranolaClient(key)
        return refresh_folder_cache(client)
```

- [ ] **Step 5.4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_app.py -v 2>&1 | tail -10`
Expected: 5 passed.

- [ ] **Step 5.5: Commit**

```bash
git add src/granola_sync/app.py tests/test_app.py
git commit -m "feat(app): expose API key + folder discovery to the bridge"
```

## Task 6 · Mapping bridge methods + `pick_folder`

**Files:**
- Modify: `src/granola_sync/app.py`
- Modify: `tests/test_app.py`

- [ ] **Step 6.1: Write the failing tests**

Append to `tests/test_app.py`:

```python
# ---------------------------------------------------------------------------
# Mappings
# ---------------------------------------------------------------------------

def test_list_create_update_delete_mapping(api, tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH", str(cfg))

    assert api.list_mappings() == []

    m = api.create_mapping("fol_a", "CS101", str(tmp_path / "CS101"))
    assert m["extract"] == "both"

    m2 = api.update_mapping("fol_a", extract="ai_notes")
    assert m2["extract"] == "ai_notes"

    assert api.delete_mapping("fol_a") is True
    assert api.list_mappings() == []


def test_create_mapping_accepts_extract(api, tmp_path, monkeypatch):
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH",
                        str(tmp_path / "config.json"))
    m = api.create_mapping("fol_a", "CS101", str(tmp_path / "CS101"),
                           extract="transcript")
    assert m["extract"] == "transcript"


# ---------------------------------------------------------------------------
# pick_folder
# ---------------------------------------------------------------------------

def test_pick_folder_returns_path(api):
    fake_window = MagicMock()
    fake_window.create_file_dialog.return_value = ("/Users/x/Notes/CS101",)
    with patch.object(webview, "windows", [fake_window]):
        result = api.pick_folder()
    assert result == "/Users/x/Notes/CS101"


def test_pick_folder_returns_none_on_cancel(api):
    fake_window = MagicMock()
    fake_window.create_file_dialog.return_value = None
    with patch.object(webview, "windows", [fake_window]):
        assert api.pick_folder() is None


def test_pick_folder_no_window_returns_none(api):
    with patch.object(webview, "windows", []):
        assert api.pick_folder() is None
```

Also add at the top of the test file (with other imports):

```python
import webview
```

- [ ] **Step 6.2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_app.py -v -k "mapping or pick_folder" 2>&1 | tail -15`
Expected: 5 failures.

- [ ] **Step 6.3: Implement mapping methods + `pick_folder`**

Add to the `Api` class in `src/granola_sync/app.py`:

```python
    # ---------- Mappings ----------

    def list_mappings(self) -> list[dict]:
        return list_mappings()

    def create_mapping(
        self,
        folder_id: str,
        folder_name: str,
        local_path: str,
        extract: str = "both",
    ) -> dict:
        return create_mapping(folder_id, folder_name, local_path, extract=extract)

    def update_mapping(self, folder_id: str, **fields) -> dict:
        return update_mapping(folder_id, **fields)

    def delete_mapping(self, folder_id: str) -> bool:
        return delete_mapping(folder_id)

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
```

- [ ] **Step 6.4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_app.py -v 2>&1 | tail -10`
Expected: 10 passed.

- [ ] **Step 6.5: Commit**

```bash
git add src/granola_sync/app.py tests/test_app.py
git commit -m "feat(app): expose mappings CRUD + native folder picker"
```

## Task 7 · `progress.py` — threaded sync with JS callbacks

**Files:**
- Create: `src/granola_sync/progress.py`
- Create: `tests/test_progress.py`

The progress helper runs sync in a background thread and pushes structured events to the frontend via `window.evaluate_js("window.granolaSync.onSyncProgress(<json>)")`.

- [ ] **Step 7.1: Write the failing tests**

Create `tests/test_progress.py`:

```python
"""Tests for src/granola_sync/progress.py — threaded sync + JS callbacks."""
import json
import threading
import time
from unittest.mock import MagicMock

import pytest

from granola_sync.progress import SyncProgressRunner


@pytest.fixture
def fake_window():
    return MagicMock()


def _wait_for(predicate, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_runner_emits_done_event_on_empty_sync(fake_window):
    runner = SyncProgressRunner(fake_window)
    sync_id = runner.start(lambda emit: emit({"type": "done", "sync_id": "x",
                                              "written": 0, "skipped": 0,
                                              "errors": 0, "elapsed_ms": 0}))
    assert sync_id

    assert _wait_for(lambda: fake_window.evaluate_js.called)
    call_arg = fake_window.evaluate_js.call_args[0][0]
    assert "onSyncProgress" in call_arg
    assert '"type": "done"' in call_arg


def test_runner_emits_error_event_on_exception(fake_window):
    runner = SyncProgressRunner(fake_window)
    def task(emit):
        raise RuntimeError("boom")
    runner.start(task)

    assert _wait_for(lambda: any(
        '"type": "error"' in c[0][0]
        for c in fake_window.evaluate_js.call_args_list
    ))


def test_runner_assigns_unique_sync_ids(fake_window):
    runner = SyncProgressRunner(fake_window)
    a = runner.start(lambda emit: None)
    b = runner.start(lambda emit: None)
    assert a != b


def test_runner_cancel_sets_flag(fake_window):
    runner = SyncProgressRunner(fake_window)
    seen_cancel = threading.Event()
    def task(emit, is_cancelled=lambda: False):
        # poll cancellation flag
        while not is_cancelled():
            time.sleep(0.01)
        seen_cancel.set()
    sync_id = runner.start(task)
    time.sleep(0.05)
    runner.cancel(sync_id)
    assert seen_cancel.wait(timeout=1.0)
```

- [ ] **Step 7.2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_progress.py -v 2>&1 | tail -5`
Expected: `ModuleNotFoundError: No module named 'granola_sync.progress'`.

- [ ] **Step 7.3: Implement `progress.py`**

Create `src/granola_sync/progress.py`:

```python
"""
Threaded sync runner + JS callback bridge.

A :class:`SyncProgressRunner` owns one or more background sync tasks.
Each task is given an ``emit`` callable; whatever it emits gets
serialized as JSON and pushed into the frontend via
``window.evaluate_js("window.granolaSync.onSyncProgress(<json>)")``.

Cancellation is cooperative: tasks are passed an ``is_cancelled``
callable they should poll.
"""

from __future__ import annotations

import json
import threading
import uuid
from typing import Callable


_JS_HANDLER = "window.granolaSync && window.granolaSync.onSyncProgress"


class SyncProgressRunner:
    def __init__(self, window):
        self._window = window
        self._cancel_flags: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def start(
        self,
        task: Callable[..., None],
    ) -> str:
        """
        Kick off ``task`` in a background daemon thread.

        ``task`` is invoked as either ``task(emit)`` or
        ``task(emit, is_cancelled=...)`` (it can declare the second
        positional arg if it wants cancellation support).

        Returns a unique ``sync_id``.
        """
        sync_id = uuid.uuid4().hex
        cancel = threading.Event()
        with self._lock:
            self._cancel_flags[sync_id] = cancel

        def emit(event: dict) -> None:
            payload = json.dumps(event)
            # JS guard so we don't crash if window.granolaSync isn't set up yet
            self._window.evaluate_js(
                f"if ({_JS_HANDLER}) {_JS_HANDLER}({payload});"
            )

        def runner_target():
            try:
                # Pass is_cancelled only if the task asks for it
                import inspect
                params = inspect.signature(task).parameters
                if "is_cancelled" in params:
                    task(emit, is_cancelled=cancel.is_set)
                else:
                    task(emit)
            except Exception as exc:
                emit({"type": "error", "sync_id": sync_id, "message": str(exc)})
            finally:
                with self._lock:
                    self._cancel_flags.pop(sync_id, None)

        threading.Thread(target=runner_target, daemon=True).start()
        return sync_id

    def cancel(self, sync_id: str) -> bool:
        """Signal cancellation. Returns True if the sync was active."""
        with self._lock:
            flag = self._cancel_flags.get(sync_id)
        if flag is None:
            return False
        flag.set()
        return True
```

- [ ] **Step 7.4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_progress.py -v 2>&1 | tail -5`
Expected: 4 passed.

- [ ] **Step 7.5: Commit**

```bash
git add src/granola_sync/progress.py tests/test_progress.py
git commit -m "feat(progress): threaded sync runner with JS callback bridge"
```

## Task 8 · Sync bridge methods (`start_sync`, `cancel_sync`, `sync_dry_run`)

**Files:**
- Modify: `src/granola_sync/app.py`
- Modify: `tests/test_app.py`

- [ ] **Step 8.1: Write the failing tests**

Append to `tests/test_app.py`:

```python
# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

def test_sync_dry_run_returns_serializable_results(api, tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH", str(cfg))
    # No mappings configured → empty list
    assert api.sync_dry_run() == []


def test_start_sync_returns_sync_id_and_streams_done(api, tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr("granola_sync.mappings._DEFAULT_CONFIG_PATH", str(cfg))
    monkeypatch.setattr("granola_sync.state._DEFAULT_STATE_PATH",
                        str(tmp_path / ".state.json"))
    api.set_api_key("grn_testkey")
    fake_window = MagicMock()
    with patch.object(webview, "windows", [fake_window]):
        sync_id = api.start_sync()
    assert isinstance(sync_id, str) and len(sync_id) > 0

    # The runner should have emitted a 'done' event with 0 counts
    import time
    deadline = time.time() + 2.0
    while time.time() < deadline:
        if any('"type": "done"' in c[0][0]
               for c in fake_window.evaluate_js.call_args_list):
            return
        time.sleep(0.02)
    pytest.fail("sync 'done' event was not emitted in 2s")


def test_cancel_sync_returns_bool(api):
    fake_window = MagicMock()
    with patch.object(webview, "windows", [fake_window]):
        # Cancelling an unknown sync_id returns False
        assert api.cancel_sync("not-a-real-id") is False
```

- [ ] **Step 8.2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_app.py -v -k "sync" 2>&1 | tail -10`
Expected: 3 failures.

- [ ] **Step 8.3: Implement sync methods**

Add to `src/granola_sync/app.py`:

```python
import time
from .sync import sync_dry_run, sync_all, sync_folder
from .progress import SyncProgressRunner
```

Inside the `Api` class:

```python
    # Created lazily once a window exists
    _runner: SyncProgressRunner | None = None

    def _get_runner(self) -> SyncProgressRunner | None:
        if self._runner is None and webview.windows:
            self._runner = SyncProgressRunner(webview.windows[0])
        return self._runner

    # ---------- Sync ----------

    def sync_dry_run(self) -> list[dict]:
        """Return what would be written, without writing anything."""
        results = sync_dry_run()
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
            t0 = time.time()
            try:
                results = sync_folder(folder_id) if folder_id else sync_all()
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
                            "sync_id": "",   # filled in below
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
            except Exception as exc:
                emit({"type": "error", "sync_id": "", "message": str(exc)})

        return runner.start(task)

    def cancel_sync(self, sync_id: str) -> bool:
        runner = self._get_runner()
        if runner is None:
            return False
        return runner.cancel(sync_id)
```

- [ ] **Step 8.4: Run tests to verify they pass**

Run: `python3 -m pytest tests/ -v 2>&1 | tail -5`
Expected: 108 passed (95 + 13 from Phases 1–2).

- [ ] **Step 8.5: Commit**

```bash
git add src/granola_sync/app.py tests/test_app.py
git commit -m "feat(app): expose sync_dry_run / start_sync / cancel_sync via bridge"
```

---

# Phase 3 · Frontend scaffold

Set up the Vite + React + TS + Tailwind + shadcn/ui project under `frontend/`. End of phase: `npm run dev` serves a "Hello Granola Sync" page; `python3 -m granola_sync --frontend-url http://localhost:5173` opens a pywebview window pointed at it.

## Task 9 · Bootstrap Vite + React + TypeScript

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`

- [ ] **Step 9.1: Scaffold via `npm create vite@latest`**

Run:
```bash
cd "/Users/julianleitersdorf/Desktop/Coding Projects/AI-Class-Notes-Pipeline"
npm create vite@latest frontend -- --template react-ts -y
cd frontend && npm install
```

Verify the dev server boots:
```bash
npm run dev -- --port 5173
```
Open http://localhost:5173 in a browser; expect the Vite + React default page. `Ctrl-C` to stop.

- [ ] **Step 9.2: Lock Vite to relative paths so `file://` works**

Edit `frontend/vite.config.ts`:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  // Use relative paths so the bundle works when loaded from file:// inside pywebview
  base: "./",
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: { port: 5173, strictPort: true },
  build: { outDir: "dist", assetsDir: "assets" },
});
```

Confirm `frontend/tsconfig.json` has:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  }
}
```

(Merge with the rest of the existing config; do not delete other keys.)

- [ ] **Step 9.3: Replace the default `App.tsx` with a placeholder**

Replace `frontend/src/App.tsx`:

```tsx
export default function App() {
  return (
    <div style={{ minHeight: "100vh", display: "flex",
                  alignItems: "center", justifyContent: "center",
                  background: "#08080a", color: "#e5e5e8",
                  fontFamily: "Inter, -apple-system, sans-serif" }}>
      <div>
        <h1 style={{ fontSize: 24, margin: 0 }}>Granola Sync</h1>
        <p style={{ color: "#888", fontSize: 13 }}>Frontend booted ✓</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 9.4: Verify dev server still works**

Run: `cd frontend && npm run dev -- --port 5173` and confirm "Granola Sync — Frontend booted ✓" appears. `Ctrl-C` to stop.

- [ ] **Step 9.5: Commit**

```bash
cd ..
git add frontend/
git commit -m "feat(frontend): scaffold Vite + React + TS project"
```

## Task 10 · Add Tailwind + theme tokens

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/tailwind.config.js`, `frontend/postcss.config.js`, `frontend/src/theme.css`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 10.1: Install Tailwind v3**

Run:
```bash
cd frontend
npm install -D tailwindcss@^3.4 postcss autoprefixer
npx tailwindcss init -p
```

This creates `tailwind.config.js` and `postcss.config.js`.

- [ ] **Step 10.2: Configure Tailwind to scan the React sources**

Edit `frontend/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg:        "var(--bg)",
        elevated:  "var(--bg-elevated)",
        surface:   "var(--surface)",
        border:    "var(--border)",
        "border-accent": "var(--border-accent)",
        accent:    "var(--accent)",
        "accent-hover": "var(--accent-hover)",
        success:   "var(--success)",
        warning:   "var(--warning)",
        error:     "var(--error)",
      },
      textColor: {
        DEFAULT:   "var(--text)",
        muted:     "var(--text-muted)",
        faint:     "var(--text-faint)",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
```

- [ ] **Step 10.3: Create theme tokens**

Create `frontend/src/theme.css`:

```css
:root {
  --bg: #08080a;
  --bg-elevated: #0e0e11;
  --surface: #141418;
  --border: #1f1f24;
  --border-accent: #2b2d4d;
  --text: #e5e5e8;
  --text-muted: #888888;
  --text-faint: #5a5a62;
  --accent: #5e6ad2;
  --accent-hover: #7079e0;
  --success: #28ca41;
  --warning: #ffbd2e;
  --error: #ff5f57;
}

@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #root {
  height: 100%;
  margin: 0;
  font-family: var(--font-sans, Inter, -apple-system, sans-serif);
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
  -webkit-font-smoothing: antialiased;
}
```

- [ ] **Step 10.4: Wire it in `main.tsx`**

Replace `frontend/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./theme.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 10.5: Verify the theme applies**

Update `frontend/src/App.tsx` to use Tailwind utilities:

```tsx
export default function App() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div>
        <h1 className="text-2xl font-semibold">Granola Sync</h1>
        <p className="text-muted text-sm mt-1">Frontend booted ✓</p>
      </div>
    </div>
  );
}
```

Run `npm run dev -- --port 5173`, open http://localhost:5173. Expect: dark background, near-white heading, muted-grey subtext. `Ctrl-C`.

- [ ] **Step 10.6: Commit**

```bash
cd ..
git add frontend/package.json frontend/package-lock.json frontend/tailwind.config.js frontend/postcss.config.js frontend/src/theme.css frontend/src/main.tsx frontend/src/App.tsx
git commit -m "feat(frontend): add Tailwind v3 + theme tokens (Linear dark)"
```

## Task 11 · Wire the bridge — typed `api.ts` + `--frontend-url` flag

**Files:**
- Create: `frontend/src/api.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `src/granola_sync/__main__.py`

- [ ] **Step 11.1: Create the typed bridge wrapper**

Create `frontend/src/api.ts`:

```typescript
/**
 * Typed wrapper around window.pywebview.api.
 *
 * The wrapper waits for pywebview to inject the API (it does so
 * after window.onload), then returns a thin proxy that just calls
 * through. All methods return Promises.
 */

export type Folder = { id: string; object: "folder"; name: string };

export type Mapping = {
  folder_id: string;
  folder_name: string;
  local_path: string;
  extract: "both" | "ai_notes" | "transcript";
};

export type FolderCache = {
  folders: Folder[];
  refreshed_at: string | null;
};

export type DryRunResult = {
  folder_id: string;
  folder_name: string;
  local_path: string;
  written: number;
  skipped: number;
  errors: number;
};

export type SyncEvent =
  | { type: "note"; sync_id: string; folder_id: string;
      status: "written" | "skipped" | "error"; note_id: string;
      title: string; file_path?: string; error?: string }
  | { type: "folder_done"; sync_id: string; folder_id: string;
      folder_name: string; written: number; skipped: number; errors: number }
  | { type: "done"; sync_id: string; written: number; skipped: number;
      errors: number; elapsed_ms: number }
  | { type: "error"; sync_id: string; message: string };

export interface PywebviewApi {
  get_version(): Promise<string>;
  get_api_key(): Promise<string | null>;
  set_api_key(key: string): Promise<void>;
  load_cached_folders(): Promise<FolderCache>;
  refresh_folders(): Promise<FolderCache>;
  list_mappings(): Promise<Mapping[]>;
  create_mapping(folder_id: string, folder_name: string,
                 local_path: string, extract?: Mapping["extract"]): Promise<Mapping>;
  update_mapping(folder_id: string, fields: Partial<Mapping>): Promise<Mapping>;
  delete_mapping(folder_id: string): Promise<boolean>;
  pick_folder(title?: string): Promise<string | null>;
  sync_dry_run(): Promise<DryRunResult[]>;
  start_sync(folder_id?: string): Promise<string>;
  cancel_sync(sync_id: string): Promise<boolean>;
}

declare global {
  interface Window {
    pywebview?: { api: PywebviewApi };
    granolaSync?: { onSyncProgress: (event: SyncEvent) => void };
  }
}

/** Resolves once pywebview has injected window.pywebview.api. */
export function waitForBridge(timeoutMs = 5000): Promise<PywebviewApi> {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    function check() {
      if (window.pywebview?.api) {
        resolve(window.pywebview.api);
        return;
      }
      if (Date.now() - start > timeoutMs) {
        reject(new Error("pywebview bridge not available"));
        return;
      }
      setTimeout(check, 50);
    }
    check();
  });
}
```

- [ ] **Step 11.2: Use the bridge from `App.tsx` (smoke test)**

Replace `frontend/src/App.tsx`:

```tsx
import { useEffect, useState } from "react";
import { waitForBridge } from "./api";

export default function App() {
  const [version, setVersion] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    waitForBridge()
      .then((api) => api.get_version())
      .then(setVersion)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div>
        <h1 className="text-2xl font-semibold">Granola Sync</h1>
        {version && <p className="text-muted text-sm mt-1">v{version}</p>}
        {error && <p className="text-error text-sm mt-1">{error}</p>}
      </div>
    </div>
  );
}
```

- [ ] **Step 11.3: Add `--frontend-url` and `--tkinter` to `__main__.py`**

Replace `src/granola_sync/__main__.py`:

```python
"""Entry point for `python -m granola_sync` / `granola-sync`."""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(prog="granola-sync")
    parser.add_argument(
        "--tkinter",
        action="store_true",
        help="Launch the V1 Tkinter GUI instead of the new pywebview frontend.",
    )
    parser.add_argument(
        "--frontend-url",
        default=None,
        help="Load the frontend from this URL (e.g. http://localhost:5173 "
             "during development). Defaults to the bundled frontend/dist.",
    )
    args = parser.parse_args()

    if args.tkinter:
        from .gui import main as gui_main
        gui_main()
        return

    from .app import launch
    launch(dev_url=args.frontend_url)


if __name__ == "__main__":
    main()
```

- [ ] **Step 11.4: Smoke-test the bridge**

In one terminal:
```bash
cd "/Users/julianleitersdorf/Desktop/Coding Projects/AI-Class-Notes-Pipeline/frontend"
npm run dev -- --port 5173
```

In another terminal:
```bash
cd "/Users/julianleitersdorf/Desktop/Coding Projects/AI-Class-Notes-Pipeline"
pip install -e . -q
python3 -m granola_sync --frontend-url http://localhost:5173
```

Expected: a desktop window opens titled "Granola Sync" showing the heading and a version like `v1.1.0`. Close the window.

Also verify `--tkinter` still works:
```bash
python3 -m granola_sync --tkinter
```
Expected: the V1 Tkinter window appears.

- [ ] **Step 11.5: Commit**

```bash
git add frontend/src/api.ts frontend/src/App.tsx src/granola_sync/__main__.py
git commit -m "feat(frontend): typed bridge + pywebview launches React app"
```

## Task 12 · Add Zustand for state + verify build

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/state/index.ts`, `frontend/src/state/setup.ts`, `frontend/src/state/mappings.ts`, `frontend/src/state/sync.ts`, `frontend/src/state/ui.ts`

- [ ] **Step 12.1: Install Zustand + helpers**

```bash
cd frontend
npm install zustand
npm install -D clsx tailwind-merge
```

Create `frontend/src/lib/cn.ts`:

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 12.2: Create the store slices**

Create `frontend/src/state/setup.ts`:

```typescript
import type { Folder } from "../api";

export interface SetupSlice {
  apiKey: string | null;
  folders: Folder[];
  foldersRefreshedAt: string | null;
  setApiKey: (key: string | null) => void;
  setFolders: (folders: Folder[], refreshedAt: string | null) => void;
}

export const createSetupSlice = (set: any): SetupSlice => ({
  apiKey: null,
  folders: [],
  foldersRefreshedAt: null,
  setApiKey: (apiKey) => set({ apiKey }),
  setFolders: (folders, foldersRefreshedAt) => set({ folders, foldersRefreshedAt }),
});
```

Create `frontend/src/state/mappings.ts`:

```typescript
import type { Mapping } from "../api";

export interface MappingsSlice {
  mappings: Mapping[];
  setMappings: (mappings: Mapping[]) => void;
}

export const createMappingsSlice = (set: any): MappingsSlice => ({
  mappings: [],
  setMappings: (mappings) => set({ mappings }),
});
```

Create `frontend/src/state/sync.ts`:

```typescript
import type { SyncEvent } from "../api";

export interface SyncSlice {
  syncId: string | null;
  running: boolean;
  events: SyncEvent[];
  startSync: (id: string) => void;
  appendEvent: (event: SyncEvent) => void;
  endSync: () => void;
  clearLog: () => void;
}

export const createSyncSlice = (set: any): SyncSlice => ({
  syncId: null,
  running: false,
  events: [],
  startSync: (id) => set({ syncId: id, running: true, events: [] }),
  appendEvent: (event) =>
    set((s: any) => ({ events: [...s.events, event].slice(-500) })),
  endSync: () => set({ running: false, syncId: null }),
  clearLog: () => set({ events: [] }),
});
```

Create `frontend/src/state/ui.ts`:

```typescript
export type Tab = "setup" | "mappings" | "sync";

export interface UISlice {
  currentTab: Tab;
  wizardStep: 1 | 2 | 3 | 4 | null;
  toast: { kind: "error" | "info"; message: string } | null;
  setTab: (tab: Tab) => void;
  setWizardStep: (step: 1 | 2 | 3 | 4 | null) => void;
  showToast: (kind: "error" | "info", message: string) => void;
  clearToast: () => void;
}

export const createUISlice = (set: any): UISlice => ({
  currentTab: "setup",
  wizardStep: null,
  toast: null,
  setTab: (currentTab) => set({ currentTab }),
  setWizardStep: (wizardStep) => set({ wizardStep }),
  showToast: (kind, message) => set({ toast: { kind, message } }),
  clearToast: () => set({ toast: null }),
});
```

Create `frontend/src/state/index.ts`:

```typescript
import { create } from "zustand";
import { createSetupSlice, type SetupSlice } from "./setup";
import { createMappingsSlice, type MappingsSlice } from "./mappings";
import { createSyncSlice, type SyncSlice } from "./sync";
import { createUISlice, type UISlice } from "./ui";

export type Store = SetupSlice & MappingsSlice & SyncSlice & UISlice;

export const useStore = create<Store>()((set) => ({
  ...createSetupSlice(set),
  ...createMappingsSlice(set),
  ...createSyncSlice(set),
  ...createUISlice(set),
}));
```

- [ ] **Step 12.3: Verify the build**

```bash
cd frontend && npm run build
```

Expected: `dist/` is created, no TypeScript errors. (Vite reports build size — should be under ~250 kB.)

- [ ] **Step 12.4: Smoke-test pip-install path**

```bash
cd ..
python3 -m granola_sync
```

Expected: a desktop window opens showing the React app from `frontend/dist`. Version string appears. Close.

- [ ] **Step 12.5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/lib frontend/src/state
git commit -m "feat(frontend): Zustand store with setup/mappings/sync/ui slices"
```

---

# Phase 4 · Setup tab

End of phase: Setup tab is fully functional. Replaces the React App's placeholder.

## Task 13 · Components: Button, Card, Input, Tabs

**Files:**
- Create: `frontend/src/components/Button.tsx`, `frontend/src/components/Card.tsx`, `frontend/src/components/Input.tsx`, `frontend/src/components/Tabs.tsx`

- [ ] **Step 13.1: Write the components**

Create `frontend/src/components/Button.tsx`:

```tsx
import { ButtonHTMLAttributes } from "react";
import { cn } from "../lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger";

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      {...props}
      className={cn(
        "px-3 py-1.5 text-[12px] rounded-md font-medium transition-colors",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        variant === "primary" &&
          "bg-accent text-white hover:bg-accent-hover",
        variant === "secondary" &&
          "border border-border text-[color:var(--text)] hover:bg-surface",
        variant === "ghost" &&
          "text-[color:var(--text-muted)] hover:text-[color:var(--text)]",
        variant === "danger" &&
          "text-error hover:bg-error/10",
        className
      )}
    />
  );
}
```

Create `frontend/src/components/Card.tsx`:

```tsx
import { HTMLAttributes } from "react";
import { cn } from "../lib/cn";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...props}
      className={cn(
        "rounded-[10px] border border-border bg-elevated p-4",
        className
      )}
    />
  );
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      {...props}
      className={cn("text-[13px] font-semibold mb-1", className)}
    />
  );
}

export function CardSubtitle({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p {...props} className={cn("text-[11px] text-muted mb-3", className)} />
  );
}
```

Create `frontend/src/components/Input.tsx`:

```tsx
import { InputHTMLAttributes } from "react";
import { cn } from "../lib/cn";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={cn(
        "w-full bg-surface border border-border rounded-[5px] px-2.5 py-1.5",
        "text-[12px] text-[color:var(--text)] placeholder:text-faint",
        "focus:outline-none focus:border-[color:var(--border-accent)]",
        className
      )}
    />
  );
}
```

Create `frontend/src/components/Tabs.tsx`:

```tsx
import { ReactNode } from "react";
import { cn } from "../lib/cn";
import { useStore, type Tab } from "../state";

const TABS: { id: Tab; label: string }[] = [
  { id: "setup", label: "Setup" },
  { id: "mappings", label: "Mappings" },
  { id: "sync", label: "Sync" },
];

export function TabStrip() {
  const { currentTab, setTab } = useStore();
  return (
    <div className="flex border-b border-border px-3.5">
      {TABS.map((t) => (
        <button
          key={t.id}
          onClick={() => setTab(t.id)}
          className={cn(
            "px-3 py-2.5 text-[12px] transition-colors",
            currentTab === t.id
              ? "text-[color:var(--text)] border-b-[1.5px] border-accent font-medium"
              : "text-[color:var(--text-muted)] hover:text-[color:var(--text)]"
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function TabPanels({ children }: { children: ReactNode }) {
  return <div className="flex-1 overflow-auto p-4">{children}</div>;
}
```

Note `state.ts` uses `type Tab` re-export. Add to `frontend/src/state/index.ts`:

```typescript
export type { Tab } from "./ui";
```

- [ ] **Step 13.2: Verify the build**

```bash
cd frontend && npm run build
```

Expected: no errors.

- [ ] **Step 13.3: Commit**

```bash
cd ..
git add frontend/src/components frontend/src/state/index.ts
git commit -m "feat(frontend): Button/Card/Input/Tabs primitives"
```

## Task 14 · Setup tab

**Files:**
- Create: `frontend/src/screens/Setup/index.tsx`, `frontend/src/lib/format.ts`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 14.1: Helper for relative time**

Create `frontend/src/lib/format.ts`:

```typescript
export function formatRelativeTime(iso: string | null): string {
  if (!iso) return "never";
  const when = new Date(iso);
  if (Number.isNaN(when.getTime())) return iso;
  const secs = Math.max(0, (Date.now() - when.getTime()) / 1000);
  if (secs < 60) return "just now";
  if (secs < 3600) return `${Math.floor(secs / 60)} min ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)} hr ago`;
  const days = Math.floor(secs / 86400);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}
```

- [ ] **Step 14.2: Build the Setup tab**

Create `frontend/src/screens/Setup/index.tsx`:

```tsx
import { useEffect, useState } from "react";
import { waitForBridge } from "../../api";
import { useStore } from "../../state";
import { Card, CardTitle, CardSubtitle } from "../../components/Card";
import { Button } from "../../components/Button";
import { Input } from "../../components/Input";
import { formatRelativeTime } from "../../lib/format";

export function SetupTab() {
  const { apiKey, folders, foldersRefreshedAt, setApiKey, setFolders, showToast } = useStore();
  const [keyDraft, setKeyDraft] = useState(apiKey ?? "");
  const [showKey, setShowKey] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    waitForBridge().then(async (api) => {
      const saved = await api.get_api_key();
      if (saved) {
        setApiKey(saved);
        setKeyDraft(saved);
      }
      const cache = await api.load_cached_folders();
      setFolders(cache.folders, cache.refreshed_at);
    });
  }, [setApiKey, setFolders]);

  async function save() {
    if (!keyDraft.trim()) return;
    const api = await waitForBridge();
    await api.set_api_key(keyDraft.trim());
    setApiKey(keyDraft.trim());
    showToast("info", "API key saved.");
  }

  async function refresh() {
    setRefreshing(true);
    try {
      const api = await waitForBridge();
      const cache = await api.refresh_folders();
      setFolders(cache.folders, cache.refreshed_at);
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardTitle>Granola API key</CardTitle>
        <CardSubtitle>
          Get yours from the Granola desktop app → Settings → API → Create new key.
        </CardSubtitle>
        <div className="flex gap-2">
          <Input
            type={showKey ? "text" : "password"}
            value={keyDraft}
            onChange={(e) => setKeyDraft(e.target.value)}
            placeholder="grn_..."
            autoComplete="off"
            spellCheck={false}
          />
          <Button variant="secondary" onClick={() => setShowKey((s) => !s)}>
            {showKey ? "Hide" : "Show"}
          </Button>
          <Button onClick={save} disabled={!keyDraft.trim()}>
            Save
          </Button>
        </div>
      </Card>

      <Card>
        <div className="flex items-center justify-between mb-2">
          <CardTitle className="mb-0">Discovered folders</CardTitle>
          <Button variant="ghost" onClick={refresh} disabled={refreshing}>
            {refreshing ? "Refreshing…" : "⟳ Refresh"}
          </Button>
        </div>
        <CardSubtitle>
          {folders.length} folder(s) · refreshed {formatRelativeTime(foldersRefreshedAt)}
        </CardSubtitle>
        <div className="flex flex-col gap-1 max-h-[280px] overflow-auto pr-1">
          {folders.length === 0 ? (
            <p className="text-faint text-[11px] py-2">
              No folders cached. Save your API key and click Refresh.
            </p>
          ) : (
            folders.map((f) => (
              <div
                key={f.id}
                className="bg-surface border border-border rounded-[5px] px-3 py-1.5 text-[11px]"
              >
                {f.name}
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}
```

- [ ] **Step 14.3: Wire Tabs + Setup into `App.tsx`**

Replace `frontend/src/App.tsx`:

```tsx
import { TabStrip, TabPanels } from "./components/Tabs";
import { SetupTab } from "./screens/Setup";
import { useStore } from "./state";

export default function App() {
  const tab = useStore((s) => s.currentTab);
  return (
    <div className="min-h-screen flex flex-col">
      <TabStrip />
      <TabPanels>
        {tab === "setup" && <SetupTab />}
        {tab === "mappings" && <Placeholder name="Mappings" />}
        {tab === "sync" && <Placeholder name="Sync" />}
      </TabPanels>
    </div>
  );
}

function Placeholder({ name }: { name: string }) {
  return <p className="text-muted text-[12px]">{name} tab — coming next.</p>;
}
```

- [ ] **Step 14.4: Smoke-test**

```bash
cd frontend && npm run dev -- --port 5173 &
cd .. && python3 -m granola_sync --frontend-url http://localhost:5173
```

Expected: Setup tab is selected by default. API key field shows your saved key (if `config.json` already has one); Save updates it. Click Refresh — folders populate within ~30 s. Switch tabs to confirm placeholders appear. Close window, `Ctrl-C` the dev server.

- [ ] **Step 14.5: Commit**

```bash
git add frontend/src/screens/Setup frontend/src/lib/format.ts frontend/src/App.tsx
git commit -m "feat(frontend): Setup tab — API key card + folder discovery"
```

---

# Phase 5 · Mappings tab

End of phase: a user can add, edit (extract config), and delete mappings from the Mappings tab. Drag-drop is stubbed via a "+ New mapping" dialog.

## Task 15 · Mappings tab layout + load mappings

**Files:**
- Create: `frontend/src/screens/Mappings/index.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 15.1: Build the Mappings tab**

Create `frontend/src/screens/Mappings/index.tsx`:

```tsx
import { useEffect, useState } from "react";
import { waitForBridge, type Mapping } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";
import { NewMappingDialog } from "./NewMappingDialog";
import { ConfigPopover } from "./ConfigPopover";

const EXTRACT_LABELS: Record<Mapping["extract"], string> = {
  both: "Both",
  ai_notes: "AI notes only",
  transcript: "Transcript only",
};

export function MappingsTab() {
  const { folders, mappings, setMappings, showToast } = useStore();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [openConfig, setOpenConfig] = useState<string | null>(null);

  useEffect(() => {
    waitForBridge()
      .then((api) => api.list_mappings())
      .then(setMappings)
      .catch((e) => showToast("error", String(e?.message ?? e)));
  }, [setMappings, showToast]);

  const mappedFolderIds = new Set(mappings.map((m) => m.folder_id));

  return (
    <div className="flex gap-4 h-full">
      {/* Left pane: Granola folders */}
      <div className="flex-1 flex flex-col gap-1.5">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] uppercase tracking-wider text-faint font-semibold">
            Granola · {folders.length} folders
          </span>
        </div>
        {folders.length === 0 ? (
          <p className="text-faint text-[11px]">
            No folders cached. Refresh on the Setup tab.
          </p>
        ) : (
          folders.map((f) => {
            const isMapped = mappedFolderIds.has(f.id);
            return (
              <div
                key={f.id}
                className={`bg-surface border rounded-[6px] px-3 py-2 text-[11px] flex items-center gap-2
                  ${isMapped ? "border-[color:var(--border-accent)]" : "border-border text-faint"}`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${isMapped ? "bg-accent" : "bg-border"}`}
                />
                {f.name}
              </div>
            );
          })
        )}
      </div>

      {/* Arrows column */}
      <div className="w-6 flex flex-col pt-7 gap-1.5 items-center text-accent text-[12px]">
        {mappings.map((m) => (
          <div key={m.folder_id} className="h-7 flex items-center">→</div>
        ))}
      </div>

      {/* Right pane: Local destinations */}
      <div className="flex-1 flex flex-col gap-1.5">
        <span className="text-[10px] uppercase tracking-wider text-faint font-semibold mb-1.5">
          Local · {mappings.length} mapped
        </span>
        {mappings.map((m) => (
          <div
            key={m.folder_id}
            className="bg-surface border border-[color:var(--border-accent)] rounded-[6px] px-3 py-2 text-[11px] flex items-center gap-2 relative"
          >
            <div className="flex-1 flex flex-col">
              <span>{m.local_path}</span>
              <span className="text-[9px] text-faint">{EXTRACT_LABELS[m.extract]}</span>
            </div>
            <button
              className="text-faint hover:text-[color:var(--text)] text-[11px]"
              onClick={() => setOpenConfig(openConfig === m.folder_id ? null : m.folder_id)}
              aria-label="Configure mapping"
            >
              ⚙
            </button>
            {openConfig === m.folder_id && (
              <ConfigPopover
                mapping={m}
                onClose={() => setOpenConfig(null)}
              />
            )}
          </div>
        ))}
        <Button
          variant="secondary"
          className="mt-1.5 border-dashed text-faint"
          onClick={() => setDialogOpen(true)}
        >
          + New mapping
        </Button>
      </div>

      {dialogOpen && <NewMappingDialog onClose={() => setDialogOpen(false)} />}
    </div>
  );
}
```

Also update `frontend/src/App.tsx` to route to `MappingsTab`:

```tsx
import { TabStrip, TabPanels } from "./components/Tabs";
import { SetupTab } from "./screens/Setup";
import { MappingsTab } from "./screens/Mappings";
import { useStore } from "./state";

export default function App() {
  const tab = useStore((s) => s.currentTab);
  return (
    <div className="min-h-screen flex flex-col">
      <TabStrip />
      <TabPanels>
        {tab === "setup" && <SetupTab />}
        {tab === "mappings" && <MappingsTab />}
        {tab === "sync" && <p className="text-muted text-[12px]">Sync tab — coming next.</p>}
      </TabPanels>
    </div>
  );
}
```

- [ ] **Step 15.2: Commit (intentional broken state — dialog/popover not yet created)**

We commit the layout now and add dialog/popover in the next tasks.

```bash
git add frontend/src/screens/Mappings/index.tsx frontend/src/App.tsx
git commit -m "feat(frontend): Mappings tab layout (panes, paired rows, arrows)"
```

## Task 16 · `NewMappingDialog` (drag-drop stub)

**Files:**
- Create: `frontend/src/screens/Mappings/NewMappingDialog.tsx`

- [ ] **Step 16.1: Build the dialog**

Create `frontend/src/screens/Mappings/NewMappingDialog.tsx`:

```tsx
import { useState } from "react";
import { waitForBridge } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";
import { Card, CardTitle, CardSubtitle } from "../../components/Card";

export function NewMappingDialog({ onClose }: { onClose: () => void }) {
  const { folders, mappings, setMappings, showToast } = useStore();
  const unmapped = folders.filter(
    (f) => !mappings.some((m) => m.folder_id === f.id)
  );
  const [folderId, setFolderId] = useState<string>(unmapped[0]?.id ?? "");
  const [localPath, setLocalPath] = useState<string>("");
  const [busy, setBusy] = useState(false);

  async function pickFolder() {
    const api = await waitForBridge();
    const path = await api.pick_folder("Choose destination folder");
    if (path) setLocalPath(path);
  }

  async function create() {
    const folder = folders.find((f) => f.id === folderId);
    if (!folder || !localPath) return;
    setBusy(true);
    try {
      const api = await waitForBridge();
      await api.create_mapping(folder.id, folder.name, localPath, "both");
      const refreshed = await api.list_mappings();
      setMappings(refreshed);
      showToast("info", `Mapped ${folder.name} → ${localPath}`);
      onClose();
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-20"
      onClick={onClose}
    >
      <div onClick={(e) => e.stopPropagation()} className="w-[340px]">
        <Card>
          <CardTitle>New mapping</CardTitle>
          <CardSubtitle>
            Drag-and-drop is coming in v2.2. For now, pick a folder and destination.
          </CardSubtitle>

          <label className="text-[10px] uppercase tracking-wider text-faint font-semibold block mb-1">
            Granola folder
          </label>
          <select
            value={folderId}
            onChange={(e) => setFolderId(e.target.value)}
            className="w-full bg-surface border border-border rounded-[5px] px-2 py-1.5 text-[12px] mb-3"
          >
            {unmapped.length === 0 ? (
              <option value="">No unmapped folders</option>
            ) : (
              unmapped.map((f) => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))
            )}
          </select>

          <label className="text-[10px] uppercase tracking-wider text-faint font-semibold block mb-1">
            Local destination
          </label>
          <div className="flex gap-2 mb-4">
            <input
              readOnly
              value={localPath}
              placeholder="(none)"
              className="flex-1 bg-surface border border-border rounded-[5px] px-2.5 py-1.5 text-[12px] text-faint"
            />
            <Button variant="secondary" onClick={pickFolder}>Choose…</Button>
          </div>

          <div className="flex gap-2 justify-end">
            <Button variant="ghost" onClick={onClose}>Cancel</Button>
            <Button onClick={create} disabled={busy || !folderId || !localPath}>
              {busy ? "Creating…" : "Create mapping"}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 16.2: Commit**

```bash
git add frontend/src/screens/Mappings/NewMappingDialog.tsx
git commit -m "feat(frontend): NewMappingDialog (drag-drop stub for v2.1)"
```

## Task 17 · `ConfigPopover`

**Files:**
- Create: `frontend/src/screens/Mappings/ConfigPopover.tsx`

- [ ] **Step 17.1: Build the popover**

Create `frontend/src/screens/Mappings/ConfigPopover.tsx`:

```tsx
import { useEffect, useRef, useState } from "react";
import { waitForBridge, type Mapping } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";

const OPTIONS: { value: Mapping["extract"]; label: string }[] = [
  { value: "both",       label: "Both (notes + transcript)" },
  { value: "ai_notes",   label: "AI notes only" },
  { value: "transcript", label: "Transcript only" },
];

export function ConfigPopover({
  mapping,
  onClose,
}: {
  mapping: Mapping;
  onClose: () => void;
}) {
  const { setMappings, showToast } = useStore();
  const [extract, setExtract] = useState(mapping.extract);
  const [busy, setBusy] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [onClose]);

  async function save(newValue: Mapping["extract"]) {
    setExtract(newValue);
    setBusy(true);
    try {
      const api = await waitForBridge();
      await api.update_mapping(mapping.folder_id, { extract: newValue });
      const refreshed = await api.list_mappings();
      setMappings(refreshed);
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!confirm(`Delete mapping for ${mapping.folder_name}?`)) return;
    setBusy(true);
    try {
      const api = await waitForBridge();
      await api.delete_mapping(mapping.folder_id);
      const refreshed = await api.list_mappings();
      setMappings(refreshed);
      onClose();
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      ref={ref}
      className="absolute right-0 top-full mt-1 w-[260px] bg-elevated border border-border rounded-[8px] p-3 z-10 shadow-xl"
    >
      <p className="text-[10px] uppercase tracking-wider text-faint font-semibold mb-2">
        Extract
      </p>
      <div className="flex flex-col gap-1 mb-3">
        {OPTIONS.map((opt) => (
          <label
            key={opt.value}
            className={`flex items-center gap-2 text-[12px] cursor-pointer
              ${extract === opt.value ? "text-[color:var(--text)]" : "text-muted"}`}
          >
            <input
              type="radio"
              name={`extract-${mapping.folder_id}`}
              checked={extract === opt.value}
              onChange={() => save(opt.value)}
              disabled={busy}
              className="accent-[color:var(--accent)]"
            />
            {opt.label}
          </label>
        ))}
      </div>
      <div className="border-t border-border pt-2">
        <Button variant="danger" onClick={remove} disabled={busy} className="w-full">
          Delete mapping
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 17.2: Smoke-test**

```bash
cd frontend && npm run dev -- --port 5173 &
cd .. && python3 -m granola_sync --frontend-url http://localhost:5173
```

In the window: Setup → save key → refresh folders → switch to Mappings → click "+ New mapping" → pick a folder, click "Choose…" (OS dialog opens), pick a local path, click Create. New row appears with arrow + ⚙ icon. Click ⚙ → popover with three radio options + Delete. Toggle extract → status persists. Delete removes the row.

Close window, `Ctrl-C` dev server.

- [ ] **Step 17.3: Commit**

```bash
git add frontend/src/screens/Mappings/ConfigPopover.tsx
git commit -m "feat(frontend): per-mapping config popover (extract + delete)"
```

---

# Phase 6 · Sync tab

End of phase: Sync tab can run dry-run + live sync, with progress streamed from Python.

## Task 18 · Sync tab + progress streaming

**Files:**
- Create: `frontend/src/screens/Sync/index.tsx`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 18.1: Register the global `onSyncProgress` handler**

The Python side calls `window.granolaSync.onSyncProgress(event)`. We register a global handler that fans events into the Zustand store.

Edit `frontend/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { useStore } from "./state";
import type { SyncEvent } from "./api";
import "./theme.css";

window.granolaSync = {
  onSyncProgress(event: SyncEvent) {
    useStore.getState().appendEvent(event);
    if (event.type === "done" || event.type === "error") {
      useStore.getState().endSync();
    }
  },
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 18.2: Build the Sync tab**

Create `frontend/src/screens/Sync/index.tsx`:

```tsx
import { useState } from "react";
import { waitForBridge, type SyncEvent } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";
import { Card, CardTitle, CardSubtitle } from "../../components/Card";

function eventLine(e: SyncEvent): { color: string; text: string } | null {
  if (e.type === "note") {
    if (e.status === "written") return { color: "text-success", text: `✓ Written: ${e.title}` };
    if (e.status === "skipped") return { color: "text-faint",   text: `○ Skipped: ${e.title}` };
    return { color: "text-error", text: `✗ Error: ${e.title} — ${e.error ?? ""}` };
  }
  if (e.type === "folder_done") {
    return {
      color: "text-muted",
      text: `— ${e.folder_name}: ${e.written} written, ${e.skipped} skipped, ${e.errors} errors`,
    };
  }
  if (e.type === "done") {
    return {
      color: "text-[color:var(--text)]",
      text: `Done — ${e.written} written, ${e.skipped} skipped, ${e.errors} errors (${(e.elapsed_ms / 1000).toFixed(1)}s)`,
    };
  }
  return { color: "text-error", text: `Sync error: ${e.message}` };
}

export function SyncTab() {
  const { running, events, syncId, startSync, clearLog, showToast } = useStore();
  const [dryRunResult, setDryRunResult] = useState<string | null>(null);

  async function dryRun() {
    try {
      const api = await waitForBridge();
      const results = await api.sync_dry_run();
      const w = results.reduce((s, r) => s + r.written, 0);
      const k = results.reduce((s, r) => s + r.skipped, 0);
      setDryRunResult(`${w} would be written, ${k} already up-to-date`);
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    }
  }

  async function runSync() {
    try {
      clearLog();
      const api = await waitForBridge();
      const id = await api.start_sync();
      startSync(id);
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    }
  }

  async function cancel() {
    if (!syncId) return;
    const api = await waitForBridge();
    await api.cancel_sync(syncId);
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      <Card>
        <CardTitle>Run a sync</CardTitle>
        <CardSubtitle>
          Dry run shows what would change. Sync now fetches and writes Markdown.
        </CardSubtitle>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={dryRun} disabled={running}>
            Dry run
          </Button>
          {running ? (
            <Button variant="danger" onClick={cancel}>Cancel sync</Button>
          ) : (
            <Button onClick={runSync}>Sync now</Button>
          )}
          <Button variant="ghost" onClick={clearLog} disabled={events.length === 0}>
            Clear log
          </Button>
        </div>
        {dryRunResult && (
          <p className="text-muted text-[11px] mt-2">{dryRunResult}</p>
        )}
      </Card>

      <Card className="flex-1 flex flex-col">
        <CardTitle>Activity log</CardTitle>
        <div className="flex-1 overflow-auto font-mono text-[11px] leading-relaxed mt-2 min-h-[180px]">
          {events.length === 0 ? (
            <p className="text-faint">No activity yet.</p>
          ) : (
            events.map((e, i) => {
              const line = eventLine(e);
              if (!line) return null;
              return <div key={i} className={line.color}>{line.text}</div>;
            })
          )}
        </div>
      </Card>
    </div>
  );
}
```

- [ ] **Step 18.3: Route Sync into `App.tsx`**

Replace the last placeholder in `frontend/src/App.tsx`:

```tsx
import { TabStrip, TabPanels } from "./components/Tabs";
import { SetupTab } from "./screens/Setup";
import { MappingsTab } from "./screens/Mappings";
import { SyncTab } from "./screens/Sync";
import { useStore } from "./state";

export default function App() {
  const tab = useStore((s) => s.currentTab);
  return (
    <div className="min-h-screen flex flex-col">
      <TabStrip />
      <TabPanels>
        {tab === "setup" && <SetupTab />}
        {tab === "mappings" && <MappingsTab />}
        {tab === "sync" && <SyncTab />}
      </TabPanels>
    </div>
  );
}
```

- [ ] **Step 18.4: Smoke-test end-to-end**

```bash
cd frontend && npm run dev -- --port 5173 &
cd .. && python3 -m granola_sync --frontend-url http://localhost:5173
```

In the window: Setup → key + refresh. Mappings → add a mapping pointing at a writable directory. Sync → click Dry run (shows count). Click Sync now (live progress lines stream in). Done event appears with elapsed time.

Verify files actually got written:
```bash
ls "<the mapped local path>"
```

Close window, `Ctrl-C` dev server.

- [ ] **Step 18.5: Commit**

```bash
git add frontend/src/screens/Sync frontend/src/main.tsx frontend/src/App.tsx
git commit -m "feat(frontend): Sync tab with live progress + Cancel"
```

---

# Phase 7 · First-launch wizard

End of phase: a fresh user (no `config.json`) gets the 4-step wizard automatically.

## Task 19 · Wizard shell + step progress UI

**Files:**
- Create: `frontend/src/screens/Wizard/index.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 19.1: Build the wizard shell**

Create `frontend/src/screens/Wizard/index.tsx`:

```tsx
import { useStore } from "../../state";
import { Step1ApiKey } from "./Step1ApiKey";
import { Step2Folders } from "./Step2Folders";
import { Step3Mapping } from "./Step3Mapping";
import { Step4Done } from "./Step4Done";

export function Wizard() {
  const step = useStore((s) => s.wizardStep);
  if (step === null) return null;

  return (
    <div className="fixed inset-0 bg-bg flex flex-col items-center justify-center p-6 z-30">
      <div className="flex gap-1.5 mb-6">
        {[1, 2, 3, 4].map((n) => (
          <span
            key={n}
            className={`w-6 h-[3px] rounded-full ${
              n <= step ? "bg-accent" : "bg-border"
            }`}
          />
        ))}
      </div>

      <p className="text-[10px] uppercase tracking-wider text-accent font-semibold mb-3">
        Step {step} of 4 ·{" "}
        {step === 1 ? "Connect" : step === 2 ? "Discover" : step === 3 ? "Map" : "Ready"}
      </p>

      <div className="w-full max-w-[340px]">
        {step === 1 && <Step1ApiKey />}
        {step === 2 && <Step2Folders />}
        {step === 3 && <Step3Mapping />}
        {step === 4 && <Step4Done />}
      </div>
    </div>
  );
}
```

- [ ] **Step 19.2: Mount the wizard at top-level**

Update `frontend/src/App.tsx`:

```tsx
import { TabStrip, TabPanels } from "./components/Tabs";
import { SetupTab } from "./screens/Setup";
import { MappingsTab } from "./screens/Mappings";
import { SyncTab } from "./screens/Sync";
import { Wizard } from "./screens/Wizard";
import { useStore } from "./state";

export default function App() {
  const tab = useStore((s) => s.currentTab);
  return (
    <div className="min-h-screen flex flex-col">
      <TabStrip />
      <TabPanels>
        {tab === "setup" && <SetupTab />}
        {tab === "mappings" && <MappingsTab />}
        {tab === "sync" && <SyncTab />}
      </TabPanels>
      <Wizard />
    </div>
  );
}
```

- [ ] **Step 19.3: Commit**

```bash
git add frontend/src/screens/Wizard/index.tsx frontend/src/App.tsx
git commit -m "feat(frontend): wizard shell + step progress UI"
```

## Task 20 · Wizard steps 1–2

**Files:**
- Create: `frontend/src/screens/Wizard/Step1ApiKey.tsx`, `frontend/src/screens/Wizard/Step2Folders.tsx`

- [ ] **Step 20.1: Step 1 — API key**

Create `frontend/src/screens/Wizard/Step1ApiKey.tsx`:

```tsx
import { useState } from "react";
import { waitForBridge } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";
import { Input } from "../../components/Input";

export function Step1ApiKey() {
  const { setApiKey, setWizardStep, showToast } = useStore();
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);

  async function next() {
    if (!key.trim()) return;
    setBusy(true);
    try {
      const api = await waitForBridge();
      await api.set_api_key(key.trim());
      setApiKey(key.trim());
      setWizardStep(2);
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="text-center">
      <h2 className="text-[16px] font-semibold mb-1">Paste your Granola API key</h2>
      <p className="text-muted text-[11px] mb-5">
        Granola desktop → Settings → API → Create new key.
      </p>
      <Input
        type="password"
        value={key}
        onChange={(e) => setKey(e.target.value)}
        placeholder="grn_..."
        autoFocus
        spellCheck={false}
        autoComplete="off"
        className="mb-4"
      />
      <Button onClick={next} disabled={!key.trim() || busy}>
        {busy ? "Saving…" : "Continue →"}
      </Button>
    </div>
  );
}
```

- [ ] **Step 20.2: Step 2 — Folders**

Create `frontend/src/screens/Wizard/Step2Folders.tsx`:

```tsx
import { useEffect, useState } from "react";
import { waitForBridge } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";

export function Step2Folders() {
  const { folders, setFolders, setWizardStep, showToast } = useStore();
  const [pickedId, setPickedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [pendingFolder, setPendingFolder] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const api = await waitForBridge();
        const cache = await api.refresh_folders();
        setFolders(cache.folders, cache.refreshed_at);
      } catch (e: any) {
        showToast("error", String(e?.message ?? e));
      } finally {
        setLoading(false);
      }
    })();
  }, [setFolders, showToast]);

  function next() {
    if (!pickedId) return;
    setPendingFolder(pickedId);
    setWizardStep(3);
  }

  // Stash the picked folder for Step 3 via a global cache (avoids
  // adding a separate slice). Step 3 reads `wizardPickedFolderId`.
  useEffect(() => {
    if (pendingFolder) (window as any).__wizardPickedFolderId = pendingFolder;
  }, [pendingFolder]);

  return (
    <div className="text-center">
      <h2 className="text-[16px] font-semibold mb-1">
        {loading ? "Discovering folders…" : `Found ${folders.length} folders`}
      </h2>
      <p className="text-muted text-[11px] mb-5">
        Pick one to start with — you can map the rest later.
      </p>

      <div className="flex flex-col gap-1.5 mb-5 max-h-[180px] overflow-auto pr-1">
        {loading ? (
          <p className="text-faint text-[11px] py-3">This can take ~30 s.</p>
        ) : folders.length === 0 ? (
          <p className="text-faint text-[11px] py-3">No folders found.</p>
        ) : (
          folders.map((f) => (
            <button
              key={f.id}
              onClick={() => setPickedId(f.id)}
              className={`text-left bg-surface border rounded-[5px] px-3 py-1.5 text-[11px] transition-colors
                ${pickedId === f.id
                  ? "border-[color:var(--border-accent)] text-[color:var(--text)]"
                  : "border-border text-muted hover:text-[color:var(--text)]"}`}
            >
              {f.name}
            </button>
          ))
        )}
      </div>

      <div className="flex gap-2 justify-center">
        <Button variant="secondary" onClick={() => setWizardStep(1)}>Back</Button>
        <Button onClick={next} disabled={!pickedId}>Continue →</Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 20.3: Commit**

```bash
git add frontend/src/screens/Wizard/Step1ApiKey.tsx frontend/src/screens/Wizard/Step2Folders.tsx
git commit -m "feat(frontend): wizard steps 1 (api key) + 2 (folders)"
```

## Task 21 · Wizard steps 3–4

**Files:**
- Create: `frontend/src/screens/Wizard/Step3Mapping.tsx`, `frontend/src/screens/Wizard/Step4Done.tsx`

- [ ] **Step 21.1: Step 3 — First mapping**

Create `frontend/src/screens/Wizard/Step3Mapping.tsx`:

```tsx
import { useState } from "react";
import { waitForBridge } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";

export function Step3Mapping() {
  const { folders, setMappings, setWizardStep, showToast } = useStore();
  const pickedId: string | null = (window as any).__wizardPickedFolderId ?? null;
  const folder = folders.find((f) => f.id === pickedId);
  const [localPath, setLocalPath] = useState<string>("");
  const [busy, setBusy] = useState(false);

  async function pickFolder() {
    const api = await waitForBridge();
    const path = await api.pick_folder(`Choose destination for ${folder?.name ?? ""}`);
    if (path) setLocalPath(path);
  }

  async function next() {
    if (!folder || !localPath) return;
    setBusy(true);
    try {
      const api = await waitForBridge();
      await api.create_mapping(folder.id, folder.name, localPath, "both");
      const refreshed = await api.list_mappings();
      setMappings(refreshed);
      setWizardStep(4);
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="text-center">
      <h2 className="text-[16px] font-semibold mb-1">
        Where should <span className="text-accent">{folder?.name ?? "this folder"}</span> go on your Mac?
      </h2>
      <p className="text-muted text-[11px] mb-5">
        Pick a local folder — Granola notes will be written there as Markdown.
      </p>

      <button
        onClick={pickFolder}
        className={`w-full mb-4 px-4 py-6 rounded-[8px] text-[12px] transition-colors
          ${localPath
            ? "bg-surface border border-[color:var(--border-accent)] text-[color:var(--text)]"
            : "bg-elevated border border-dashed border-border text-muted hover:text-[color:var(--text)]"}`}
      >
        {localPath ? localPath : "Click to choose a folder"}
      </button>

      {folder && localPath && (
        <p className="text-muted text-[11px] mb-5 font-mono">
          {folder.name} → {localPath}
        </p>
      )}

      <div className="flex gap-2 justify-center">
        <Button variant="secondary" onClick={() => setWizardStep(2)}>Back</Button>
        <Button onClick={next} disabled={busy || !localPath}>
          {busy ? "Saving…" : "Continue →"}
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 21.2: Step 4 — Done**

Create `frontend/src/screens/Wizard/Step4Done.tsx`:

```tsx
import { useState } from "react";
import { waitForBridge } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";

export function Step4Done() {
  const { mappings, setWizardStep, setTab, startSync, clearLog, showToast } = useStore();
  const [busy, setBusy] = useState(false);

  function finish() {
    setWizardStep(null);
    setTab("mappings");
  }

  async function syncNow() {
    const first = mappings[0];
    if (!first) return finish();
    setBusy(true);
    try {
      const api = await waitForBridge();
      clearLog();
      const id = await api.start_sync(first.folder_id);
      startSync(id);
      setWizardStep(null);
      setTab("sync");
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
      setBusy(false);
    }
  }

  return (
    <div className="text-center">
      <h2 className="text-[20px] font-semibold mb-1">You're set up.</h2>
      <p className="text-muted text-[12px] mb-6">
        {mappings.length} mapping ready. Sync now or come back later.
      </p>
      <div className="flex gap-2 justify-center">
        <Button variant="secondary" onClick={finish} disabled={busy}>
          Maybe later
        </Button>
        <Button onClick={syncNow} disabled={busy || mappings.length === 0}>
          {busy ? "Starting…" : "Sync now"}
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 21.3: Commit**

```bash
git add frontend/src/screens/Wizard/Step3Mapping.tsx frontend/src/screens/Wizard/Step4Done.tsx
git commit -m "feat(frontend): wizard steps 3 (first mapping) + 4 (done)"
```

## Task 22 · First-launch detection + re-run from Setup

**Files:**
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/screens/Setup/index.tsx`

- [ ] **Step 22.1: Auto-open wizard when no API key is saved**

Edit `frontend/src/main.tsx` — after the `granolaSync` registration and before `createRoot`, add:

```tsx
async function bootstrap() {
  try {
    const { waitForBridge } = await import("./api");
    const api = await waitForBridge();
    const saved = await api.get_api_key();
    if (!saved) {
      useStore.getState().setWizardStep(1);
    }
  } catch {
    // Bridge unavailable in tests — leave wizard closed.
  }
}
bootstrap();
```

- [ ] **Step 22.2: Add "Re-run setup" link to the Setup tab**

In `frontend/src/screens/Setup/index.tsx`, add at the bottom of the rendered output (just before the closing `</div>` of the outer flex container):

```tsx
<button
  onClick={() => useStore.getState().setWizardStep(1)}
  className="text-muted text-[11px] hover:text-[color:var(--text)] self-start"
>
  Re-run setup wizard
</button>
```

(Make sure `useStore` is imported at the top — it already is.)

- [ ] **Step 22.3: Smoke-test fresh install**

Temporarily move your `config.json` aside, then relaunch:

```bash
mv config.json config.json.bak
cd frontend && npm run dev -- --port 5173 &
cd .. && python3 -m granola_sync --frontend-url http://localhost:5173
```

Expected: the wizard appears immediately, full-screen. Complete all 4 steps (use a real API key + a real local folder). Restore:

```bash
mv config.json.bak config.json   # or keep the wizard-created one
```

`Ctrl-C` the dev server.

- [ ] **Step 22.4: Commit**

```bash
git add frontend/src/main.tsx frontend/src/screens/Setup/index.tsx
git commit -m "feat(frontend): first-launch wizard auto-open + re-run link"
```

---

# Phase 8 · Polish, tests, CI, docs

End of phase: V2.1 is releasable. CHANGELOG bumped to 2.1.0, README/CLAUDE.md mention the new GUI, CI runs the full test matrix.

## Task 23 · ErrorBoundary + Toast UI

**Files:**
- Create: `frontend/src/components/ErrorBoundary.tsx`, `frontend/src/components/Toast.tsx`
- Modify: `frontend/src/main.tsx`, `frontend/src/App.tsx`

- [ ] **Step 23.1: Build ErrorBoundary**

Create `frontend/src/components/ErrorBoundary.tsx`:

```tsx
import { Component, ReactNode } from "react";

export class ErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6">
          <div className="max-w-[420px] text-center">
            <h1 className="text-[16px] font-semibold mb-2">Something broke.</h1>
            <pre className="text-[11px] text-error font-mono bg-surface border border-border rounded p-3 overflow-auto mb-4">
              {this.state.error.message}
            </pre>
            <button
              onClick={() => location.reload()}
              className="px-3 py-1.5 bg-accent text-white rounded-md text-[12px]"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
```

- [ ] **Step 23.2: Build Toast**

Create `frontend/src/components/Toast.tsx`:

```tsx
import { useEffect } from "react";
import { useStore } from "../state";

export function Toast() {
  const { toast, clearToast } = useStore();

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(clearToast, 4000);
    return () => clearTimeout(t);
  }, [toast, clearToast]);

  if (!toast) return null;
  return (
    <div
      className={`fixed bottom-4 right-4 z-50 max-w-[320px] rounded-[8px] px-3 py-2 text-[12px]
        ${toast.kind === "error"
          ? "bg-error text-white"
          : "bg-elevated border border-border text-[color:var(--text)]"}`}
      onClick={clearToast}
    >
      {toast.message}
    </div>
  );
}
```

- [ ] **Step 23.3: Wire them in**

Update `frontend/src/main.tsx` — wrap `<App />` with the boundary:

```tsx
import { ErrorBoundary } from "./components/ErrorBoundary";

// inside createRoot(...).render(...):
<React.StrictMode>
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
</React.StrictMode>
```

Update `frontend/src/App.tsx` — mount the toast:

```tsx
import { Toast } from "./components/Toast";

// inside the App return, after <Wizard />:
<Toast />
```

- [ ] **Step 23.4: Commit**

```bash
git add frontend/src/components/ErrorBoundary.tsx frontend/src/components/Toast.tsx frontend/src/main.tsx frontend/src/App.tsx
git commit -m "feat(frontend): ErrorBoundary + Toast"
```

## Task 24 · Vitest unit tests

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/lib/format.test.ts`, `frontend/src/state/store.test.ts`, `frontend/src/screens/Setup/Setup.test.tsx`

- [ ] **Step 24.1: Install Vitest + RTL**

```bash
cd frontend
npm install -D vitest @vitest/coverage-v8 jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

Create `frontend/vitest.config.ts`:

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    coverage: { reporter: ["text", "html"] },
  },
});
```

Create `frontend/vitest.setup.ts`:

```typescript
import "@testing-library/jest-dom";
```

In `frontend/package.json`, add scripts:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:e2e": "playwright test"
  }
}
```

- [ ] **Step 24.2: Format helper tests**

Create `frontend/src/lib/format.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { formatRelativeTime } from "./format";

describe("formatRelativeTime", () => {
  beforeEach(() => { vi.useFakeTimers(); vi.setSystemTime(new Date("2026-06-03T12:00:00Z")); });
  afterEach(() => { vi.useRealTimers(); });

  it("returns 'never' for null", () => {
    expect(formatRelativeTime(null)).toBe("never");
  });

  it("returns 'just now' under a minute", () => {
    expect(formatRelativeTime("2026-06-03T11:59:30Z")).toBe("just now");
  });

  it("returns '5 min ago'", () => {
    expect(formatRelativeTime("2026-06-03T11:55:00Z")).toBe("5 min ago");
  });

  it("returns '2 hr ago'", () => {
    expect(formatRelativeTime("2026-06-03T10:00:00Z")).toBe("2 hr ago");
  });

  it("returns '1 day ago' singular", () => {
    expect(formatRelativeTime("2026-06-02T12:00:00Z")).toBe("1 day ago");
  });

  it("returns 'N days ago' plural", () => {
    expect(formatRelativeTime("2026-05-30T12:00:00Z")).toBe("4 days ago");
  });

  it("falls back to the raw string when unparseable", () => {
    expect(formatRelativeTime("not a date")).toBe("not a date");
  });
});
```

- [ ] **Step 24.3: Store tests**

Create `frontend/src/state/store.test.ts`:

```typescript
import { describe, it, expect, beforeEach } from "vitest";
import { useStore } from "./index";

describe("useStore", () => {
  beforeEach(() => {
    // Reset store between tests
    useStore.setState({
      apiKey: null, folders: [], foldersRefreshedAt: null,
      mappings: [],
      syncId: null, running: false, events: [],
      currentTab: "setup", wizardStep: null, toast: null,
    });
  });

  it("setApiKey updates the slice", () => {
    useStore.getState().setApiKey("grn_x");
    expect(useStore.getState().apiKey).toBe("grn_x");
  });

  it("appendEvent caps log at 500 entries", () => {
    const { appendEvent } = useStore.getState();
    for (let i = 0; i < 510; i++) {
      appendEvent({ type: "note", sync_id: "x", folder_id: "f", status: "written",
                    note_id: `n${i}`, title: `T${i}` });
    }
    expect(useStore.getState().events.length).toBe(500);
  });

  it("endSync clears syncId and running", () => {
    const { startSync, endSync } = useStore.getState();
    startSync("abc");
    expect(useStore.getState().running).toBe(true);
    endSync();
    expect(useStore.getState().syncId).toBe(null);
    expect(useStore.getState().running).toBe(false);
  });

  it("setWizardStep advances", () => {
    useStore.getState().setWizardStep(2);
    expect(useStore.getState().wizardStep).toBe(2);
  });
});
```

- [ ] **Step 24.4: Run the tests**

```bash
npm test
```

Expected: all tests pass. Note any failures and fix before continuing.

- [ ] **Step 24.5: Commit**

```bash
cd ..
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts frontend/vitest.setup.ts frontend/src/lib/format.test.ts frontend/src/state/store.test.ts
git commit -m "test(frontend): Vitest + format helper + store tests"
```

## Task 25 · Playwright E2E smoke (wizard happy path)

**Files:**
- Create: `frontend/playwright.config.ts`, `frontend/tests/e2e/wizard.spec.ts`

- [ ] **Step 25.1: Install Playwright**

```bash
cd frontend
npm install -D @playwright/test
npx playwright install --with-deps chromium
```

Create `frontend/playwright.config.ts`:

```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30000,
  use: { baseURL: "http://localhost:5173", headless: true },
  webServer: {
    command: "npm run dev -- --port 5173",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
  },
});
```

- [ ] **Step 25.2: Mock bridge fixture + happy-path test**

Create `frontend/tests/e2e/wizard.spec.ts`:

```typescript
import { test, expect } from "@playwright/test";

// We inject a mock pywebview.api before the React app boots.
const MOCK_BRIDGE = `
  window.pywebview = {
    api: {
      get_version: () => Promise.resolve("2.1.0"),
      get_api_key: () => Promise.resolve(null),
      set_api_key: (k) => Promise.resolve(),
      load_cached_folders: () => Promise.resolve({ folders: [], refreshed_at: null }),
      refresh_folders: () => Promise.resolve({
        folders: [
          { id: "fol_cs101", object: "folder", name: "CS101 Lectures" },
          { id: "fol_algo",  object: "folder", name: "Algorithms" },
        ],
        refreshed_at: new Date().toISOString(),
      }),
      list_mappings: () => Promise.resolve([]),
      create_mapping: (folder_id, folder_name, local_path, extract) =>
        Promise.resolve({ folder_id, folder_name, local_path, extract }),
      pick_folder: () => Promise.resolve("/tmp/CS101"),
      sync_dry_run: () => Promise.resolve([]),
      start_sync: () => Promise.resolve("sync-id"),
      cancel_sync: () => Promise.resolve(true),
      update_mapping: () => Promise.resolve({}),
      delete_mapping: () => Promise.resolve(true),
    },
  };
`;

test("wizard happy path: key → folder → mapping → done", async ({ page }) => {
  await page.addInitScript(MOCK_BRIDGE);
  await page.goto("/");

  // Step 1: API key
  await expect(page.getByText(/Paste your Granola API key/i)).toBeVisible();
  await page.locator('input[type="password"]').fill("grn_e2e");
  await page.getByRole("button", { name: /continue/i }).click();

  // Step 2: Folders
  await expect(page.getByText(/Found 2 folders/i)).toBeVisible({ timeout: 5000 });
  await page.getByText("CS101 Lectures").click();
  await page.getByRole("button", { name: /continue/i }).click();

  // Step 3: Pick folder
  await page.getByText(/Click to choose a folder/i).click();
  await expect(page.getByText("/tmp/CS101")).toBeVisible();
  await page.getByRole("button", { name: /continue/i }).click();

  // Step 4: Done
  await expect(page.getByText(/You're set up/i)).toBeVisible();
  await page.getByRole("button", { name: /maybe later/i }).click();

  // Wizard dismissed → Mappings tab is active
  await expect(page.getByText(/Mappings/i)).toBeVisible();
});
```

- [ ] **Step 25.3: Run the E2E**

```bash
npx playwright test
```

Expected: 1 test passes. Fix any selector mismatches by inspecting the actual rendered text. (The test is intentionally loose with regex selectors.)

- [ ] **Step 25.4: Commit**

```bash
cd ..
git add frontend/playwright.config.ts frontend/tests/e2e
git commit -m "test(frontend): Playwright E2E for wizard happy path"
```

## Task 26 · `Makefile` + `pyproject.toml` package-data + CI workflow

**Files:**
- Create: `Makefile`, `.github/workflows/ci.yml`
- Modify: `pyproject.toml`

- [ ] **Step 26.1: Makefile**

Create `Makefile` in repo root:

```makefile
.PHONY: dev build test test-py test-fe test-e2e clean

dev:
	cd frontend && npm run dev -- --port 5173 & \
	python3 -m granola_sync --frontend-url http://localhost:5173

build:
	cd frontend && npm install && npm run build

test: test-py test-fe

test-py:
	python3 -m pytest tests/ -v

test-fe:
	cd frontend && npm test

test-e2e:
	cd frontend && npx playwright test

clean:
	rm -rf frontend/node_modules frontend/dist
	find . -name "__pycache__" -type d -exec rm -rf {} +
```

- [ ] **Step 26.2: Include frontend/dist in the wheel via `_frontend/` mirror**

Setuptools can only include files that live **inside** the package source tree. The `make build` target copies `frontend/dist` into `src/granola_sync/_frontend/` and `pyproject.toml` declares that as package data.

Update the Makefile's `build` target (replace the existing one):

```makefile
build:
	cd frontend && npm install && npm run build
	rm -rf src/granola_sync/_frontend
	cp -r frontend/dist src/granola_sync/_frontend
```

In `pyproject.toml`, add (merging with existing `[tool.setuptools.*]`; do not duplicate):

```toml
[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
granola_sync = ["_frontend/**/*"]
```

Append to `.gitignore`:

```
# Built-in copy of the React bundle (populated by `make build`)
src/granola_sync/_frontend/
```

- [ ] **Step 26.3: CI workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  python:
    strategy:
      fail-fast: false
      matrix:
        os: [macos-latest, ubuntu-latest]
        python: ["3.10", "3.12"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python }}" }
      - run: pip install -e .
      - run: python -m pytest tests/ -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci
      - run: cd frontend && npm test
      - run: cd frontend && npm run build

  e2e:
    runs-on: ubuntu-latest
    needs: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci
      - run: cd frontend && npx playwright install --with-deps chromium
      - run: cd frontend && npx playwright test
```

- [ ] **Step 26.4: Smoke-test locally**

```bash
make test-py
make test-fe
```

Both should pass.

- [ ] **Step 26.5: Commit**

```bash
git add Makefile pyproject.toml .github/workflows/ci.yml
git commit -m "build: Makefile, package-data for frontend/dist, CI matrix"
```

## Task 27 · Release docs

**Files:**
- Modify: `CHANGELOG.md`, `CLAUDE.md`, `docs/versions/v2.md`, `docs/versions/README.md`
- Create: `docs/versions/v2.1.md`

- [ ] **Step 27.1: CHANGELOG entry for 2.1.0**

In `CHANGELOG.md`, replace the `[Unreleased]` block:

```markdown
## [Unreleased]

_(no unreleased changes)_

## [2.1.0] — 2026-06-03

### Added
- **New default GUI: React + PyWebView**. `python -m granola_sync` and the `granola-sync` CLI now launch a modern desktop window (Vite + React + Tailwind + shadcn/ui, Linear-style dark) backed by the existing `granola_sync` library via a JS↔Python bridge.
- **First-launch wizard** — 4 steps (API key → discover folders → first mapping → done). Auto-opens when no API key is saved; re-runnable from the Setup tab.
- **Per-mapping `extract` config** — choose Both / AI notes only / Transcript only per mapping. Defaults to "Both" for backward compat with V1 mappings.
- **Live sync progress** streamed from Python to the frontend via `window.evaluate_js`. Cancel mid-sync.
- **`--tkinter` flag** keeps the V1 Tkinter GUI reachable as a fallback.
- New `Api` class (`granola_sync.app.Api`) exposes the library to JavaScript.
- 24+ new tests (bridge, progress runner, frontend Vitest + Playwright E2E).

### Changed
- Default entry point now opens pywebview instead of Tkinter. Use `--tkinter` to opt back into V1.
- `note_to_markdown` accepts an optional `extract` kwarg; V1 callers without it are unaffected.

[Unreleased]: https://github.com/Jrleitersdorf/AI-Class-Notes-Pipeline/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/Jrleitersdorf/AI-Class-Notes-Pipeline/releases/tag/v2.1.0
```

(Keep the existing 1.x entries below.)

- [ ] **Step 27.2: Update CLAUDE.md**

In `CLAUDE.md`, in the package layout block, add `app.py` and `progress.py`:

```
    app.py             — JS↔Python bridge (Api class) for the PyWebView GUI
    progress.py        — threaded sync runner with JS callback streaming
```

In the "Running the GUI" section, replace with:

```
## Running the GUI

```bash
python -m granola_sync                            # default — opens React + PyWebView
python -m granola_sync --tkinter                  # fallback — V1 Tkinter GUI
python -m granola_sync --frontend-url URL         # dev — load frontend from URL
```
```

- [ ] **Step 27.3: Create `docs/versions/v2.1.md`**

Create `docs/versions/v2.1.md`:

```markdown
---
version: 2.1.0
status: FROZEN
started: 2026-06-03
shipped: 2026-06-03
---

# V2.1 — "React GUI scaffold with first-launch wizard"

Shipped per [the design spec](../superpowers/specs/2026-06-03-v2-1-react-gui-design.md).

## Shipped

- [x] PyWebView + React + TS + Vite + Tailwind + shadcn/ui frontend scaffold.
- [x] `Api` bridge class (`src/granola_sync/app.py`).
- [x] Three tabs (Setup / Mappings / Sync) at feature parity with V1.
- [x] First-launch 4-step wizard (auto-opens; re-runnable from Setup).
- [x] Per-mapping `extract` config (Both / AI notes only / Transcript only).
- [x] Live sync progress streaming via `window.evaluate_js`.
- [x] `--tkinter` fallback to V1 GUI.
- [x] CI matrix (macOS + Ubuntu × Python 3.10/3.12 × Node 20).

## Not delivered in v2.1 (deferred per spec)

- Real drag-drop in the Mappings tab → v2.2 (stubbed via "+ New mapping" dialog).
- Animations / motion polish → v2.3.
- PyInstaller packaging → v2.4.
```

- [ ] **Step 27.4: Update `docs/versions/README.md`**

In the status matrix, add a row:

```markdown
| v2.1 | **FROZEN** | [v2.1.md](v2.1.md) | 2026-06-03 |
```

(Insert below the `v2` row.)

- [ ] **Step 27.5: Bump `docs/versions/v2.md` subversion checklist**

In `docs/versions/v2.md`, mark `v2.1` complete in the "Subversions" section:

```markdown
- [x] **v2.1** — React frontend scaffold + pywebview bridge; feature parity with existing Tkinter GUI.
```

- [ ] **Step 27.6: Final test run + commit**

```bash
python3 -m pytest tests/ -v
cd frontend && npm test && cd ..
git add CHANGELOG.md CLAUDE.md docs/versions/v2.1.md docs/versions/README.md docs/versions/v2.md
git commit -m "docs(v2.1.0): CHANGELOG, CLAUDE.md, version spec frozen"
```

## Task 28 · Open PR

- [ ] **Step 28.1: Push and open the PR**

```bash
git push -u origin feat/v2-1-react-gui
gh pr create --base main --head feat/v2-1-react-gui --title "feat(v2.1.0): React + PyWebView GUI with first-launch wizard" --body "$(cat <<'EOF'
Implements [the V2.1 design spec](docs/superpowers/specs/2026-06-03-v2-1-react-gui-design.md).

## What's in
- PyWebView + React + TypeScript + Vite + Tailwind + shadcn/ui frontend in \`frontend/\`.
- New \`Api\` class in \`src/granola_sync/app.py\` exposes the library to JavaScript.
- Threaded sync runner in \`src/granola_sync/progress.py\` streams progress events.
- Three tabs (Setup / Mappings / Sync) + first-launch 4-step wizard.
- Per-mapping \`extract\` field (Both / AI notes only / Transcript only).
- \`--tkinter\` flag keeps V1 GUI reachable.
- 24+ new tests; CI matrix on macOS + Ubuntu × Python 3.10/3.12 × Node 20.

## What's not
- Real drag-and-drop is stubbed via a "+ New mapping" dialog (lands in v2.2).
- No animations yet (v2.3).
- No \`.dmg\` / \`.exe\` (v2.4).

## Test plan
- [ ] \`make test\` → both Python (95+) and frontend (10+) suites pass
- [ ] \`make test-e2e\` → Playwright wizard happy-path passes
- [ ] \`make dev\` → wizard appears on fresh install, full flow lands a Markdown file on disk
- [ ] \`python3 -m granola_sync --tkinter\` → V1 GUI opens unmodified

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-review checklist (run before considering this plan done)

The plan author runs this once before handing the plan over. Don't dispatch a subagent — just look at the spec and the plan side by side.

**Spec coverage:** Walk through each section of `docs/superpowers/specs/2026-06-03-v2-1-react-gui-design.md`:

- [x] In-scope items each map to one or more tasks (Phase 1 = library prep / extract field; Phase 2 = bridge + Api; Phase 3 = scaffold; Phase 4 = Setup tab; Phase 5 = Mappings; Phase 6 = Sync; Phase 7 = wizard; Phase 8 = polish + CI + docs).
- [x] Success criteria each have a verification step (smoke tests in Tasks 11, 17, 18, 22; CI in Task 26).
- [x] Bridge API surface — every method has a test in Tasks 4–8.
- [x] `SyncEvent` TypeScript union — defined in `api.ts` (Task 11), consumed in store (Task 12) and Sync tab (Task 18).
- [x] Wizard step table — every step has its own task (Tasks 19–21).
- [x] Theme tokens — Task 10.
- [x] Build/dev workflow — Task 26 Makefile.
- [x] Error handling matrix — ErrorBoundary, Toast (Task 23); bridge error path tests (Tasks 5, 8); pywebview crash isn't a code path (process death).
- [x] Test layers — pytest in tasks throughout; Vitest in Task 24; Playwright in Task 25; CI in Task 26.
- [x] Open questions from the spec: extract lazy migration (Task 1 implements lazy via `_normalize_mapping` on read); wizard re-entry pre-fills (Step 1 reads from saved key by passing `apiKey` initial through `useState`); multi-mapping to one local path not surfaced in UI (true — the dialog allows it implicitly but doesn't promote it); 500-line log cap (Task 12 `appendEvent.slice(-500)`).

**Placeholder scan:** No `TBD`, `TODO`, "implement later", or "similar to Task N". Every code block contains real code. Every command is concrete.

**Type consistency:** `Mapping["extract"]` is the same union everywhere (`api.ts`, `mappings.py`, `note_to_markdown`). `SyncEvent` shapes match between Python emit (Task 8) and TS union (Task 11). Function signatures referenced across tasks (`waitForBridge`, `useStore`, `formatRelativeTime`) match their definitions.

**Phase boundaries are committable:** Phases 1, 3, 4, 5, 6, 7 each end with at least one passing test run + commit. The plan does **not** require all 28 tasks to land at once — any phase boundary is a viable squash/merge point if scope needs to shrink.
