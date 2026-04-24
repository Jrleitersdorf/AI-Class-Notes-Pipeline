# Roadmap

> Uncommitted ideas. Nothing here is guaranteed or dated. Items are promoted into a
> specific version spec (`docs/versions/vN.md`) only when work on that version begins.
> Pick whichever feel most valuable at the time — these are not sliced by version.

## Under consideration

### GUI & UX
- Radial tree visualization of folder hierarchy (d3)
- Search across synced notes (local full-text, fuzzy)
- Command palette (`Cmd+K`, Linear-style)
- Keyboard shortcuts everywhere
- Note preview pane inside the GUI
- Last-synced timestamp indicators per folder / per note
- Progress streaming during long syncs (live written/skipped/error counts)
- Forest view: multiple independent root trees instead of a strict hierarchy
- Multi-pane drag arrangement (more than two panes, user arranges them)
- Inline rename / move of local notes from the GUI

### Sync & data
- Scheduled auto-sync via launchd (macOS) / Task Scheduler (Windows)
- Diff view showing what changed since last sync
- Conflict resolution when a local note is edited after sync
- Custom extraction per mapping: "AI notes only" / "transcript only" / "both" / user-defined Jinja template
- YAML frontmatter with rich metadata (Obsidian-compatible: date, tags, attendees, source URL)
- Tag propagation from Granola into the Markdown file
- iCloud / Dropbox / OneDrive path normalization so `~/Library/Mobile Documents/...` and `~/iCloud Drive/...` are treated the same
- Per-folder date-range filter (sync only notes from the last N days)

### Distribution
- Homebrew cask (`brew install --cask granola-sync`)
- Signed `.dmg` (requires $99/yr Apple Developer account)
- Signed `.exe` for Windows (Microsoft Trusted Signing at ~$120/yr, or EV cert)
- Auto-update mechanism (Sparkle for macOS, WinSparkle for Windows, or GitHub Releases polling)

### Multi-account
- Multiple Granola API keys (work vs personal) in one config
- API keys stored in OS keychain instead of plain `config.json`
- Per-account colour / label in the GUI

### Integrations
- Obsidian vault export format (wikilinks between related notes, tags)
- Notion export
- Anki flashcard generation from transcripts (LLM-powered)
- MCP server so other AI tools can read your class notes

### Power-user / API
- Webhook on sync completion (run custom scripts)
- CLI subcommands (`granola-sync list folders`, `granola-sync sync --folder CS101`)
- Typed Python async API (`asyncio` version of `sync_all`)

## Won't do

- **Hosted / SaaS version** — users would have to upload their Granola API keys to a third-party server. Privacy non-starter. See [ADR-0002](decisions/0002-local-only-no-saas.md).
- **Two-way sync** (edit locally → push back to Granola) — would need write access to the Granola API and conflict resolution is its own project. Revisit only if Granola ships a write API.
- **Telemetry / analytics** — keep it local, keep it private. If we want usage data someday, make it strictly opt-in and per-event.
