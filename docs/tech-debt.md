# Tech debt

Code-local debt (pinnable to a specific file / function / line) is tracked as GitHub Issues with the `tech-debt` label:

https://github.com/Jrleitersdorf/AI-Class-Notes-Pipeline/issues?q=label%3Atech-debt

This file tracks **systemic** debt — architectural shortcuts, cross-cutting concerns, or things that span the whole project and don't fit as a single line-level issue.

## Open

### TD-001 — `list_folders()` and `list_notes_in_folder()` are O(N) API calls
- **Impact**: a user with 200 notes triggers ~200 `GET /v1/notes/{id}` calls every time Discover Folders runs or a sync starts. At the API's rate limit (5 req/s sustained) that's ~40 s just to build the folder list.
- **Why**: the `GET /v1/notes` list endpoint does not return `folder_membership` in note summaries, so each note's full detail must be fetched to learn which folder it belongs to. Verified against the real API on 2026-04-24.
- **Status**: **partially mitigated in v1.2.0** by `folder_cache.py` — discovered folders are persisted to `.folders.json` so the GUI shows them instantly on launch. The underlying O(N) call still runs whenever the user clicks "Refresh Folders" or `refresh_folder_cache()` is invoked. Not yet resolved for the sync path (`list_notes_in_folder` still re-scans).
- **Remaining fix**: per-note cache `note_id → (folder_ids, updated_at)`; only refetch when `updated_at` changes. Would eliminate the cost on both refresh and sync paths.

### TD-002 — No integration tests against the real Granola API
- **Impact**: regressions in the REST client (auth header format, endpoint paths, pagination contract, field renames) land silently until a user reports.
- **Why deferred**: requires a dedicated test account + rate-limit-safe fixtures. All V1 tests are unit tests with mocked responses.
- **Possible fix**: record/replay with [`vcrpy`](https://vcrpy.readthedocs.io/), or a nightly smoke test in CI using a secret test API key.

### TD-003 — Tkinter GUI will be obsoleted in V2
- **Impact**: any time spent polishing `src/granola_sync/gui.py` is throwaway work.
- **Why**: V2 moves to PyWebView + React (see [ADR-0001](decisions/0001-use-pywebview-for-v2-gui.md)). The Tkinter GUI is frozen at V1's feature set and will be deleted when V2 ships.
- **Action**: don't add new features to the Tkinter GUI. Bug fixes only, and only if they're trivial.

## Resolved

_(none yet — entries move here with a reference to the PR that fixed them.)_
