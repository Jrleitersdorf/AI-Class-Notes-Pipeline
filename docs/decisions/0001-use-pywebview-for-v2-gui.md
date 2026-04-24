# ADR-0001: Use PyWebView + React for V2 GUI

- **Status**: accepted
- **Date**: 2026-04-24

## Context

V1 shipped with a Tkinter GUI that works but looks dated and has no realistic path to the
Linear/Raycast-quality polish the V2 spec calls for: drag-and-drop mapping, tree / radial
visualizations, dark mode, smooth animations, hover states.

The library (`granola_sync`) must remain usable without the GUI, so whatever framework we
pick must be a consumer of the library — no two-way coupling.

Target audience is partly non-developers, so the app must be distributable as a downloaded
`.app` / `.exe` eventually, ideally also `pip install` for Day 1.

API keys grant read access to every transcript the user has ever recorded, so the key must
never leave the user's machine.

## Decision

V2 GUI is a **React + Tailwind + shadcn/ui frontend hosted inside a [pywebview](https://pywebview.flowrl.com/) window**, with the existing `granola_sync` Python package imported directly as the backend via pywebview's JS ↔ Python bridge.

Packaging: `pip install granola-sync` first, then `PyInstaller` → `.dmg` / `.exe` on GitHub Releases.

## Alternatives considered

- **CustomTkinter** — rejected: polish ceiling too low. No realistic path to Linear-quality look. Built-in drag-drop is clunky.
- **Flet (Flutter for Python)** — rejected: modern widgets, but tree / graph visualization needs hand-rolled `CustomPaint`. 40–100 MB bundle.
- **PyQt6 / PySide6 + QML** — rejected: QML is effectively a second language. LGPL shipping nuance. `QWebEngine` notoriously breaks macOS notarization.
- **Tauri + Python sidecar** — rejected: would require learning Rust deeply enough not to fight it. Sidecar signing on macOS has open bugs.
- **Electron + Python backend** — rejected: 150 MB bundle vs ~25–40 MB for pywebview. Ships a full Chromium runtime.
- **Toga (BeeWare)** — rejected: drag-and-drop isn't shipped yet ([toga#805](https://github.com/beeware/toga/issues/805), [toga#3088](https://github.com/beeware/toga/issues/3088)). Hard blocker for the core V2 feature.
- **Hosted web app (SaaS)** — rejected separately in [ADR-0002](0002-local-only-no-saas.md).

## Consequences

- **Good**: every V2 feature (drag-drop physics, tree / radial visualization, animations, hover states, dark mode) is a solved problem in the web stack with mature libraries (`dnd-kit`, `react-flow`, `framer-motion`, `shadcn/ui`). Python stays the single source of truth — no IPC protocol to design. Bundle stays small because pywebview uses the OS-native WebView (not Chromium).
- **Trade-off**: two toolchains in the repo — Python (`src/granola_sync/`) and Node (`frontend/`). Need to learn enough React / Tailwind to build the frontend. Frontend is a build artefact, not just raw files.
- **Follow-ups**:
  - ADR on frontend state management (Zustand vs Context + useReducer) — defer until we hit real complexity.
  - PyInstaller + pywebview codesigning recipe for macOS (ad-hoc + hardened runtime for now, Developer ID later if paid).
  - Decide whether to delete the Tkinter GUI when V2 ships or keep it as a fallback — probably delete; tech debt either way.
