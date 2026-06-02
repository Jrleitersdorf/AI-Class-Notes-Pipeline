# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

_(no unreleased changes)_

## [1.2.0] — 2026-06-02

### Added
- Persistent folder cache: discovered Granola folders are saved to `.folders.json` at the project root and shown instantly when the GUI opens. The Setup tab's "Discover Folders" button is now "Refresh Folders" — it re-fetches from the API and overwrites the cache. Status label shows when folders were last refreshed (e.g. "10 folder(s) · refreshed 2 hr ago").
- New library helpers: `load_folder_cache`, `save_folder_cache`, `refresh_folder_cache`.
- 9 new tests for the folder cache (load/save round-trip, corrupted-file degradation, refresh propagation, parent-dir creation), bringing the suite to 85 tests.

### Notes
- Mitigates (does not yet resolve) [TD-001](docs/tech-debt.md): the underlying O(N) API call still runs on refresh. A future per-note incremental-refresh cache would eliminate it entirely.

## [1.1.0] — 2026-04-24

### Added
- LLM-friendly transcript formatting: lecture recordings (single microphone, no diarization) are now formatted as flowing prose paragraphs with no speaker labels. Consecutive utterances are joined into the same paragraph; a silence gap of 8 s or more starts a new paragraph.
- Multi-speaker transcripts (Zoom / seminar with diarization labels) merge consecutive same-speaker runs and render as `**Speaker A**: text` blocks. Local microphone without a diarization label shows as `**You**`.

### Fixed
- `_sanitize_filename` now replaces newlines, carriage returns, and tabs in note titles so filenames no longer break across lines on disk.

## [1.0.0] — 2026-04-23

Initial release of the `granola_sync` Python package.

### Added
- `granola_sync` Python package (`src/granola_sync/`) with a public library API: `sync_all`, `sync_folder`, `sync_dry_run`, mapping CRUD (`create_mapping`, `list_mappings`, `get_mapping`, `update_mapping`, `delete_mapping`), API key helpers (`set_api_key`, `get_api_key`), and the `GranolaClient` / `FolderSyncResult` / `NoteResult` / `GranolaAPIError` types.
- `GranolaClient` wrapping the Granola public REST API with pagination, single 429 retry, and an infinite-loop guard for broken pagination responses.
- Folder ⟷ local path mappings persisted in `config.json`.
- `.state.json` sync tracker mapping `note_id → updated_at`; unchanged notes are skipped on re-sync.
- Markdown output per note: title, date, folder membership, attendees, AI-enhanced summary, full transcript.
- Optional Tkinter GUI with Setup / Mappings / Sync tabs, launched via `python -m granola_sync` or the `granola-sync` CLI entry point.
- 73-test pytest suite covering all four modules.
- Fetch full note detail to populate `folder_membership` — the `GET /v1/notes` list endpoint omits it, so `list_folders()` and `list_notes_in_folder()` fetch each note individually to discover folder membership.

[Unreleased]: https://github.com/Jrleitersdorf/AI-Class-Notes-Pipeline/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/Jrleitersdorf/AI-Class-Notes-Pipeline/releases/tag/v1.2.0
[1.1.0]: https://github.com/Jrleitersdorf/AI-Class-Notes-Pipeline/releases/tag/v1.1.0
[1.0.0]: https://github.com/Jrleitersdorf/AI-Class-Notes-Pipeline/releases/tag/v1.0.0
