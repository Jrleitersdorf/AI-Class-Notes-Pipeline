"""
granola_sync — sync Granola meeting notes to local Markdown files.

Quick start::

    import granola_sync

    # Store your API key once (get it from Granola desktop → Settings → API)
    granola_sync.set_api_key("grn_...")

    # Discover your Granola folders
    from granola_sync import GranolaClient
    client = GranolaClient("grn_...")
    folders = client.list_folders()
    # [{"id": "fol_xxx", "name": "CS101 Lectures"}, ...]

    # Map a folder to a local directory
    granola_sync.create_mapping("fol_xxx", "CS101 Lectures", "/Users/me/Notes/CS101")

    # Sync everything
    results = granola_sync.sync_all()
    for r in results:
        print(f"{r.folder_name}: {r.written} written, {r.skipped} skipped, {r.errors} errors")
"""

from .granola_client import GranolaClient, GranolaAPIError

from .mappings import (
    create_mapping,
    list_mappings,
    get_mapping,
    update_mapping,
    delete_mapping,
    get_api_key,
    set_api_key,
)

from .state import (
    load_state,
    save_state,
    is_synced,
    mark_synced,
)

from .folder_cache import (
    load_folder_cache,
    save_folder_cache,
    refresh_folder_cache,
)

from .sync import (
    sync_all,
    sync_folder,
    sync_dry_run,
    note_to_markdown,
    FolderSyncResult,
    NoteResult,
)

__all__ = [
    # Client
    "GranolaClient",
    "GranolaAPIError",
    # Mappings
    "create_mapping",
    "list_mappings",
    "get_mapping",
    "update_mapping",
    "delete_mapping",
    "get_api_key",
    "set_api_key",
    # State
    "load_state",
    "save_state",
    "is_synced",
    "mark_synced",
    # Folder cache
    "load_folder_cache",
    "save_folder_cache",
    "refresh_folder_cache",
    # Sync
    "sync_all",
    "sync_folder",
    "sync_dry_run",
    "note_to_markdown",
    "FolderSyncResult",
    "NoteResult",
]
