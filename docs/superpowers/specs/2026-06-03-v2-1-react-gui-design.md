---
version: 2.1.0
status: PLANNED
spec_for: v2.1 (first subversion of V2)
created: 2026-06-03
related_adr: docs/decisions/0001-use-pywebview-for-v2-gui.md
parent_spec: docs/versions/v2.md
---

# V2.1 — React GUI scaffold with first-launch wizard

## Goal

Ship feature parity with the V1 Tkinter GUI inside a new PyWebView + React frontend, **plus** a first-launch wizard that gets a fresh non-developer user from "downloaded" to "first sync complete" in under 2 minutes. The Linear-style dark aesthetic and the side-by-side Mappings drag-drop are scaffolded here but only fully delivered in v2.2.

This is the foundation for V2 — every later subversion (v2.2 drag-drop, v2.3 polish, v2.4 packaging) builds on the React + bridge architecture established here.

## In scope for v2.1

- React + TypeScript + Vite + Tailwind + shadcn/ui frontend scaffold under `frontend/`.
- PyWebView bridge: new `src/granola_sync/app.py` defines an `Api` class exposed to JavaScript via `window.pywebview.api.*`.
- `python -m granola_sync` / `granola-sync` CLI launches the pywebview window (replacing Tkinter as the default).
- `--tkinter` flag retained for fallback through v2.1–v2.3.
- Three top-level tabs: **Setup · Mappings · Sync**, Linear-style dark.
- First-launch **4-step wizard**: API key → discover folders → first mapping → success/sync prompt. Re-runnable from Help menu.
- Setup tab: API key card, Discover/Refresh folders, status of last refresh.
- Mappings tab: side-by-side panes (Granola left, Local right). **Static list view** of mappings with the visual structure of the final design, but **drag-drop is stubbed** (button-based "+ New mapping" → OS picker for v2.1). Real drag-drop lands in v2.2.
- Per-mapping config popover (⚙ icon) with **Both / AI notes only / Transcript only** — wired through to a new field on each mapping in `config.json`.
- Sync tab: Dry Run + Sync Now buttons, live progress log streamed from Python via `window.evaluate_js` callbacks.
- Persistent dark theme (no system-theme auto-switch in v2.1).
- pywebview/React unit + integration tests; Python bridge tests against a mocked webview.

## Explicitly out of scope (deferred to later subversions)

- Real drag-and-drop interaction (`v2.2`).
- Arrows drawn between paired rows (`v2.2`).
- Animations, motion design, hover polish (`v2.3`).
- PyInstaller bundling and `.dmg` / `.exe` (`v2.4`).
- Homebrew cask (`v2.4`).
- Light mode / system theme switching (roadmap).
- Filesystem tree on the right pane (roadmap; we keep flat destinations list).
- Multi-account, scheduled sync, Obsidian frontmatter (roadmap, post-V2).

## Success criteria

- [ ] `python -m granola_sync` opens a pywebview window with the React frontend, no Tkinter visible.
- [ ] A user who has never used the app can: open it → wizard appears → paste API key → click Discover → pick a Granola folder + a local path → click "Sync this one now" → see a Markdown file appear on disk. **Stopwatch under 2 min from window open to file written.**
- [ ] All V1 user-facing library functions are reachable through the JS bridge (the `Api` class — see "Bridge API surface" below). Internals like `load_state` / `save_state` / `mark_synced` stay library-only and are not exposed to JS.
- [ ] Per-mapping extraction config field round-trips through `config.json` and influences what `note_to_markdown` writes.
- [ ] `--tkinter` flag still launches the V1 Tkinter GUI unmodified.
- [ ] All 85 V1 tests still pass; new bridge / frontend tests reach ≥ 80 % statement coverage on `app.py` and the React `Api` wrapper module.

## Constraints / invariants

- Library public API from V1 (`sync_all`, `sync_folder`, `create_mapping`, …) stays frozen. The bridge is a thin wrapper; it does not duplicate logic.
- No local HTTP server. The webview talks to Python only via the pywebview JS↔Python bridge.
- API keys never leave the user's machine ([ADR-0002](../../decisions/0002-local-only-no-saas.md)).
- Two toolchains in the repo (Python + Node). `frontend/dist/` is checked in **only** for tagged releases (so `pip install` works without `npm install`); during development the dev server is used and `frontend/dist/` is gitignored on feature branches.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  pywebview window  (single OS process, single Python proc)  │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐    │
│   │  React frontend  (Vite bundle, served from disk)    │    │
│   │                                                      │    │
│   │   ┌────────┐  ┌──────────┐  ┌──────┐  ┌──────────┐  │    │
│   │   │ Wizard │  │ Setup    │  │ Maps │  │ Sync     │  │    │
│   │   │ flow   │  │ tab      │  │ tab  │  │ tab      │  │    │
│   │   └────┬───┘  └────┬─────┘  └──┬───┘  └────┬─────┘  │    │
│   │        │           │           │            │        │    │
│   │        └───────────┴─────┬─────┴────────────┘        │    │
│   │                          │                            │    │
│   │              window.pywebview.api.*                   │    │
│   └─────────────────────────┬─────────────────────────────┘    │
│                             │  JS↔Python bridge               │
│   ┌─────────────────────────┴─────────────────────────────┐    │
│   │  Python  src/granola_sync/app.py                       │    │
│   │      class Api:                                        │    │
│   │          set_api_key, get_api_key                      │    │
│   │          list_mappings, create_mapping, ...            │    │
│   │          discover_folders (uses folder_cache)          │    │
│   │          sync_all, sync_folder, sync_dry_run           │    │
│   │      Stream progress: window.evaluate_js("onSync...")  │    │
│   └─────────────────────────┬─────────────────────────────┘    │
│                             │                                   │
│   ┌─────────────────────────┴─────────────────────────────┐    │
│   │  Existing  granola_sync  library  (unchanged)         │    │
│   │   granola_client · mappings · state · folder_cache    │    │
│   │   sync · note_to_markdown                              │    │
│   └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**Single Python process, single OS window, no IPC across processes.** This is the pywebview model. Crash semantics: if Python dies, the window goes with it.

### Unit responsibilities (each one a separate file / module)

| Unit | Purpose | Depends on |
|---|---|---|
| `src/granola_sync/app.py` | Defines `Api` class for the JS bridge; spawns the pywebview window. **Has no business logic** — every method delegates to the library. | pywebview, `granola_sync.*` |
| `src/granola_sync/progress.py` | Helper that runs sync in a background thread and emits progress events via `window.evaluate_js("window.granolaSync.onSyncProgress(...)")`. | pywebview (window reference) |
| `frontend/src/api.ts` | Typed wrapper around `window.pywebview.api.*`. Single source of truth for the bridge surface on the JS side. | nothing |
| `frontend/src/state/` | Zustand store: API key, mappings, discovered folders, sync state, current tab, wizard step. **No fetch logic — only state.** | `api.ts` |
| `frontend/src/screens/Wizard/` | The 4-step first-launch flow. | state, components |
| `frontend/src/screens/Setup/` | API key card + folder discovery card. | state, components |
| `frontend/src/screens/Mappings/` | Side-by-side panes, list view + ⚙ popover. | state, components |
| `frontend/src/screens/Sync/` | Dry run / sync buttons + live log. | state |
| `frontend/src/components/` | Reusable: Button, Card, Popover, EmptyState, ProgressBar, etc. (shadcn-based) | nothing |
| `frontend/src/theme.ts` | Design tokens (color, spacing, font) as CSS variables. | nothing |

Each `screens/*` directory is self-contained: it owns its routing, its layout, and its calls to the Zustand store. Internals of one screen do not import internals of another.

---

## Bridge API surface

Defined in `src/granola_sync/app.py` as `class Api`. Every method is `async`-friendly on the JS side (returns a Promise). All errors raised by Python are surfaced as JS rejections; the frontend catches them and shows a toast.

```python
class Api:
    # ---------- Setup ----------
    def get_api_key(self) -> str | None: ...
    def set_api_key(self, key: str) -> None: ...

    # ---------- Folder discovery ----------
    def load_cached_folders(self) -> dict:
        """Returns {'folders': [...], 'refreshed_at': '...'} from .folders.json."""

    def refresh_folders(self) -> dict:
        """Hits the Granola API, updates .folders.json, returns the new cache."""

    # ---------- Mappings ----------
    def list_mappings(self) -> list[dict]: ...
    def create_mapping(self, folder_id: str, folder_name: str,
                       local_path: str, extract: str = "both") -> dict: ...
    def update_mapping(self, folder_id: str, **fields) -> dict: ...
    def delete_mapping(self, folder_id: str) -> bool: ...

    # ---------- OS file picker (new) ----------
    def pick_folder(self, title: str = "Choose folder") -> str | None:
        """Opens the native folder picker. Returns the chosen path or None."""

    # ---------- Sync ----------
    def sync_dry_run(self) -> list[dict]:
        """Synchronous; returns the structured FolderSyncResult list."""

    def start_sync(self, folder_id: str | None = None) -> str:
        """
        Kicks off a sync in a background thread. Returns a sync_id.
        Progress is pushed to the frontend via
        window.evaluate_js("window.granolaSync.onSyncProgress(<json>)").
        See "Sync progress events" below for the event schema.
        """

    def cancel_sync(self, sync_id: str) -> bool: ...
```

### Sync progress events

Each call to `onSyncProgress(event)` from Python receives one of these shapes (TypeScript union):

```typescript
type SyncEvent =
  | { type: "note";        sync_id: string; folder_id: string; status: "written" | "skipped" | "error"; note_id: string; title: string; file_path?: string; error?: string; }
  | { type: "folder_done"; sync_id: string; folder_id: string; folder_name: string; written: number; skipped: number; errors: number; }
  | { type: "done";        sync_id: string; written: number; skipped: number; errors: number; elapsed_ms: number; }
  | { type: "error";       sync_id: string; message: string; };
```

The frontend appends `"note"` events to the log, updates per-folder counters on `"folder_done"`, and flips the Sync Now button back to its idle state on `"done"` or `"error"`.

```python
# (continuing the Api class definition)

    # ---------- App control ----------
    def get_version(self) -> str: ...
    def open_logs(self) -> None:
        """Opens the .state.json / logs directory in Finder/Explorer."""
```

**New library additions required** (small):

- A new `extract` field on mapping records (`"both"` | `"ai_notes"` | `"transcript"`), defaulting to `"both"` for backward compat. `note_to_markdown` reads this and omits the unwanted section.
- A `pick_folder` helper in `app.py` (uses `webview.windows[0].create_file_dialog`).
- A `progress.py` helper for the threaded sync + JS callback pattern. This belongs to the GUI layer, not the library.

---

## State management (frontend)

**Zustand** for one global store. Three slices:

- `setupSlice` — `apiKey`, `folders[]`, `foldersRefreshedAt`, status flags.
- `mappingsSlice` — `mappings[]`, currently-selected, popover open state.
- `syncSlice` — `syncId`, `progress[]` (append-only log of progress events), `running` flag.

**Not using Context+useReducer** — Zustand is one dependency that gives selector hooks for free and avoids prop-drilling without Provider boilerplate. (Open question: revisit if state grows to ~1000 LOC and we want Redux DevTools.)

The store is the **only** thing that calls `api.ts`. Screens read from the store via hooks and dispatch actions that fan out to the bridge.

---

## Tab specifications

### Setup tab

Two cards stacked:

1. **API key card** — masked input (toggle visibility), Save button, "🔑 Get your key" link that opens `https://granola.ai/settings/api` externally via `pick_folder`-style helper.
2. **Folder discovery card** — shows count + last-refreshed (`"10 folders · refreshed 2 hr ago"`) using the same `_format_relative_time` helper logic as v1.2.0. **Refresh Folders** button calls `refresh_folders`. Folder list shown below in a scrollable area.

Bottom of the tab: small "Re-run setup wizard" link that re-opens the wizard.

### Mappings tab

Side-by-side panes per the mockup. **v2.1 stubs the drag-drop**: the headline drag-drop interaction lands in v2.2 — for v2.1, mappings are created via a **+ New mapping** button at the bottom of the Local pane that:

1. Opens a small dialog: "Pick a Granola folder" (dropdown of discovered folders) + "Pick a local destination" (OS folder picker via `pick_folder`).
2. Calls `create_mapping(folder_id, folder_name, local_path, extract='both')`.
3. New row appears in the Local pane.

The visual structure (panes, arrows, ⚙ icons, paired ordering) is real and final. Only the *creation gesture* is stubbed.

Each mapping row shows: local path · "Both · N notes" sublabel · ⚙ icon. ⚙ opens a popover with three radio options (Both / AI notes only / Transcript only) and a Delete button.

### Sync tab

- Two big buttons: **Dry Run** (calls `sync_dry_run`, shows what would be written), **Sync Now** (calls `start_sync()`).
- Below: scrollable monospace log. Each progress event from `onSyncProgress` appends a colored line:
  - `"✓ Written: CS101/2026-04-21 Linear Regression.md"` (green)
  - `"○ Skipped: NLP/... (already synced)"` (grey)
  - `"✗ Error: ...: 404"` (red)
- Footer: aggregate counts ("12 written · 3 skipped · 0 errors · 4.2s elapsed").
- During sync: Sync Now button shows a spinner and becomes Cancel.

---

## Wizard flow

Single React route `/wizard` that takes over the full window. The store has a `wizardStep: 1 | 2 | 3 | 4 | null` flag; `null` means we're in normal tabs mode. Set to `null` after step 4 completes or user dismisses.

| Step | Title | Body | Primary CTA | Backend call |
|---|---|---|---|---|
| 1 | "Welcome — paste your Granola API key" | Masked input + "Get your key" external link. | "Continue →" (disabled until non-empty) | `set_api_key` |
| 2 | "Found N folders in Granola" | Scrollable list of folders. User picks one. Empty-state if 0 found. | "Continue →" (disabled until one selected) | `refresh_folders` (auto on entry) |
| 3 | "Where should this go on your Mac?" | Big drop-target with copy "Drop here or click to choose". Click triggers `pick_folder`. After path chosen, shows preview: "`CS101 Lectures` → `~/Notes/CS101`". | "Continue →" | `pick_folder` then `create_mapping` |
| 4 | "You're set up." | Summary: "1 mapping ready." Two CTAs side by side: **Sync now** (triggers `start_sync(folder_id)`) or **Maybe later**. | _(both close the wizard)_ | optional `start_sync` |

Wizard auto-appears on first launch (detected by absence of `config.json` AND absence of `granola_api_key`). Re-runnable from Help menu (Setup tab footer link).

---

## Theming / visual tokens

Defined as Tailwind theme extension + CSS variables in `frontend/src/theme.css`. Source of truth for the design language.

```css
:root {
  --bg: #08080a;
  --bg-elevated: #0e0e11;
  --surface: #141418;
  --border: #1f1f24;
  --border-accent: #2b2d4d;
  --text: #e5e5e8;
  --text-muted: #888;
  --text-faint: #5a5a62;
  --accent: #5e6ad2;
  --accent-hover: #7079e0;
  --success: #28ca41;
  --warning: #ffbd2e;
  --error: #ff5f57;
  --font-sans: "Inter", -apple-system, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
}
```

Spacing: Tailwind defaults. Border radius: 5–8px (small) / 10px (cards). Font sizes: 11px (sublabels), 12–13px (body), 14–16px (headings).

---

## Build / dev workflow

```
# Dev
cd frontend && npm install && npm run dev    # Vite at localhost:5173
python -m granola_sync --frontend-url http://localhost:5173    # webview points at dev server

# Production / pip
cd frontend && npm run build                  # → frontend/dist/
pip install -e .                              # picks up bundled frontend/dist
granola-sync                                  # opens window at file://.../frontend/dist/index.html
```

`pyproject.toml` is updated to include `frontend/dist/**` in the wheel via `[tool.setuptools.package-data]`. Without this, `pip install` from PyPI would have no frontend to show.

Add a `Makefile` with `make dev`, `make build`, `make test`.

---

## Error handling

| Failure | Surface |
|---|---|
| Bad API key (401) | Toast in Setup tab: "Key rejected. Check it and try again." Wizard step 1 shakes the input and shows the same message inline. |
| Network down during sync | Per-note error appended to log: `"✗ Error: not_xxx — network unreachable"`. Sync continues with next note. |
| Rate limited (429) | Inherits v1's single-retry; on second 429 surface to log; sync continues. |
| pywebview crash | Window closes. No persistence loss — `config.json` / `.state.json` are written incrementally. |
| Frontend JS error | Caught by a top-level React `ErrorBoundary` showing "Something broke. Reload?" with a "Copy details" button. |
| `frontend/dist` missing (e.g. user pip-installed from git without running npm build) | `app.py` detects the empty dir on startup and shows a one-page "Frontend not built. Run `npm install && npm run build` in `frontend/` or use the `--tkinter` flag." |

---

## Testing

| Layer | Tool | Coverage target |
|---|---|---|
| Library (existing) | pytest | Already at 85 tests — must stay green. |
| Bridge (`app.py`, `progress.py`) | pytest with mocked `webview.Window` | ≥ 80 % statement, every public `Api` method has a happy-path test + at least one error-path test. |
| Frontend unit | Vitest + React Testing Library | ≥ 70 % statement on screens / state / components. |
| Frontend integration | Playwright running against a mock `window.pywebview.api` injected at page load | Smoke test for the wizard happy path end-to-end. |

CI matrix: macOS + Ubuntu (Linux check, even though we ship macOS-first), Python 3.10 + 3.12, Node 20.

---

## Open questions (for v2.1 implementation; defer to a follow-up ADR if needed)

- **Per-mapping `extract` field schema migration.** v1 mappings have no `extract` field. When loaded by v2, we default missing fields to `"both"`. Should that default-write back to disk on load (eager) or only on next save (lazy)? **Lean: lazy** — never mutate user files without an explicit action.
- **Wizard re-entry.** Re-running the wizard from the Help menu — should it pre-fill the API key if one is saved? **Lean: yes**, but with a banner "You already have a key saved; click Continue to keep it."
- **Multiple Granola folders → one local path.** Should the UI allow it? Backend already does (multiple mappings can have the same `local_path`). **Lean: don't surface in UI for v2.1**; the data model allows it for power users.
- **Sync log line cap.** A 200-note sync produces hundreds of log lines. Cap at 500 in memory with "+ N earlier" header? **Lean: yes.**

---

## Related

- [ADR-0001](../../decisions/0001-use-pywebview-for-v2-gui.md) — PyWebView + React choice.
- [ADR-0002](../../decisions/0002-local-only-no-saas.md) — local-only constraint.
- [v2.md](../../versions/v2.md) — parent V2 spec.
- [v1.md](../../versions/v1.md) — frozen V1 public API surface that v2.1 must preserve.
