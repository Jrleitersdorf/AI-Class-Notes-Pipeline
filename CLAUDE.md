# CLAUDE.md

## What This Project Does

A modular Python package (`granola_sync`) that syncs Granola meeting notes to local Markdown files. It fetches notes from the Granola public API, combines the AI-enhanced summary with the raw transcript, and writes them as `.md` files into per-class local folders. Designed to be used as a library by other apps, with an optional Tkinter GUI.

## Architecture

```
src/
  granola_sync/
    __init__.py        — public API (re-exports everything)
    __main__.py        — entry point for `python -m granola_sync`
    gui.py             — optional Tkinter GUI (3 tabs: Setup, Mappings, Sync)
    granola_client.py  — Granola REST API client
    mappings.py        — CRUD for folder → local-path mappings (config.json)
    state.py           — sync state tracker (.state.json, skip unchanged notes)
    sync.py            — sync logic: fetch → convert → write
tests/
  __init__.py          — placeholder; add test files here
pyproject.toml         — build config + entry points
config.example.json    — copy to config.json and fill in
```

## Data Flow

```
sync_all() / sync_folder()
  → list_mappings()         reads config.json
  → GranolaClient.list_notes_in_folder()   paginated note listing
  → is_synced()             skip notes whose updated_at hasn't changed
  → GranolaClient.get_note(include_transcript=True)
  → note_to_markdown()      summary_markdown + transcript array → .md
  → write file to local_path/{YYYY-MM-DD} {title}.md
  → mark_synced() + save_state()
```

## Granola API

- Base URL: `https://public-api.granola.ai`
- Auth: `Authorization: Bearer grn_YOUR_KEY`
- Key endpoints:
  - `GET /v1/notes` — paginated list; supports `updated_after`, `created_after`, `cursor`
  - `GET /v1/notes/{id}?include=transcript` — full note with transcript
- Folders are **not** a separate endpoint; they are discovered from each note's `folder_membership` array.
- The API only returns notes that have a completed AI summary + transcript. Notes still processing return 404.
- Rate limit: 25 req burst / 5 req per second sustained. The client retries once on 429.

## Config File (config.json)

```json
{
  "granola_api_key": "grn_...",
  "mappings": [
    {
      "folder_id":   "fol_xxx",
      "folder_name": "CS101 Lectures",
      "local_path":  "/Users/me/Notes/CS101"
    }
  ]
}
```

Lives in the project root. All functions accept a `config_path=` keyword to override.

## State File (.state.json)

```json
{ "not_abc123": "2026-04-01T10:00:00Z", ... }
```

Maps `note_id → updated_at`. A note is only re-fetched and re-written when its `updated_at` changes. Lives in the project root. Override with `state_path=`.

## Note File Format

```
# {title}
Date: {YYYY-MM-DD}
Folders: CS101 Lectures, Algorithms
Attendees: Prof. Smith, Julian

## Notes

{summary_markdown}

---

## Transcript

**[microphone]**: text
**[speaker]**: text
```

Filename: `{YYYY-MM-DD} {sanitized_title}.md` using `created_at` date.

## Using as a Library

```python
import granola_sync

# One-time setup
granola_sync.set_api_key("grn_...")
granola_sync.create_mapping("fol_xxx", "CS101 Lectures", "/path/to/CS101")

# Sync
results = granola_sync.sync_all()

# Or target one folder
result = granola_sync.sync_folder("fol_xxx")

# Preview without writing
results = granola_sync.sync_dry_run()

# CRUD
granola_sync.list_mappings()
granola_sync.update_mapping("fol_xxx", local_path="/new/path")
granola_sync.delete_mapping("fol_xxx")
```

## Running the GUI

```bash
python -m granola_sync       # works immediately (no install needed)
# or after pip install -e .:
granola-sync
```

## Setup

```bash
pip install -r requirements.txt    # quick install
# OR for proper package install (enables `import granola_sync` from anywhere):
pip install -e .

cp config.example.json config.json
# Edit config.json: add your API key (Granola desktop → Settings → API)
```

## Key Technical Notes

**Path resolution:** `config.json` and `.state.json` default to the project root. In `mappings.py` and `state.py`, this is resolved as `Path(__file__).parent.parent.parent` (file → `granola_sync/` → `src/` → project root).

**Folder discovery:** There is no dedicated folders API endpoint. `list_folders()` works by paginating all notes and collecting unique `folder_membership` entries.

**Transcript speaker labels:** macOS recordings use `source: microphone` or `source: speaker`. iOS recordings use `source: microphone` for all entries, with an optional `diarization_label` (e.g. `Speaker A`). The converter prefers `diarization_label` when present.
