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
