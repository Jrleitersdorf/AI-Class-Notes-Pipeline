"""
Granola Sync — Tkinter GUI

A desktop window that wraps the granola_sync package. Launch with:
    python -m granola_sync
    # or after pip install -e .:
    granola-sync

The package works completely independently — this file is optional.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .granola_client import GranolaClient
from .mappings import (
    create_mapping,
    list_mappings,
    get_mapping,
    update_mapping,
    delete_mapping,
    get_api_key,
    set_api_key,
)
from .sync import sync_all, sync_dry_run


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_in_thread(fn, on_done=None):
    """Run fn() in a background thread; call on_done(result, error) on the main thread."""
    def target():
        result, error = None, None
        try:
            result = fn()
        except Exception as exc:
            error = exc
        if on_done:
            root = tk._default_root  # noqa: SLF001
            if root:
                root.after(0, lambda: on_done(result, error))
    t = threading.Thread(target=target, daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# Setup Tab
# ---------------------------------------------------------------------------

class SetupTab(ttk.Frame):
    def __init__(self, parent, app: "App"):
        super().__init__(parent, padding=16)
        self.app = app
        self._build()

    def _build(self):
        # API Key
        ttk.Label(self, text="Granola API Key", font=("", 12, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            self,
            text="Get yours: Granola desktop app → Settings → API → Create new key",
            foreground="gray",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self._key_var = tk.StringVar(value=get_api_key() or "")
        key_entry = ttk.Entry(self, textvariable=self._key_var, width=48, show="*")
        key_entry.grid(row=2, column=0, sticky="ew", padx=(0, 8))

        self._show_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self, text="Show", variable=self._show_var,
            command=lambda: key_entry.config(show="" if self._show_var.get() else "*"),
        ).grid(row=2, column=1)

        ttk.Button(self, text="Save", command=self._save_key).grid(row=2, column=2, padx=(8, 0))

        ttk.Separator(self, orient="horizontal").grid(
            row=3, column=0, columnspan=3, sticky="ew", pady=16
        )

        # Discover Folders
        ttk.Label(self, text="Discovered Folders", font=("", 12, "bold")).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            self,
            text="Folders are discovered by scanning your Granola notes. This may take a moment.",
            foreground="gray",
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self._discover_btn = ttk.Button(
            self, text="Discover Folders", command=self._discover
        )
        self._discover_btn.grid(row=6, column=0, sticky="w")

        self._status_label = ttk.Label(self, text="", foreground="gray")
        self._status_label.grid(row=6, column=1, columnspan=2, sticky="w", padx=(12, 0))

        cols = ("ID", "Name")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", height=10)
        for col in cols:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=200 if col == "Name" else 160)
        self._tree.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(8, 0))

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=7, column=3, sticky="ns", pady=(8, 0))

        self.columnconfigure(0, weight=1)
        self.rowconfigure(7, weight=1)

    def _save_key(self):
        key = self._key_var.get().strip()
        if not key:
            messagebox.showwarning("Missing key", "Please enter your Granola API key.")
            return
        set_api_key(key)
        self.app.api_key = key
        messagebox.showinfo("Saved", "API key saved to config.json.")

    def _discover(self):
        key = self._key_var.get().strip() or get_api_key()
        if not key:
            messagebox.showwarning("No API key", "Enter and save your API key first.")
            return
        self._discover_btn.config(state="disabled")
        self._status_label.config(text="Fetching folders…")
        self._tree.delete(*self._tree.get_children())

        def fetch():
            client = GranolaClient(key)
            return client.list_folders()

        def done(folders, error):
            self._discover_btn.config(state="normal")
            if error:
                self._status_label.config(text=f"Error: {error}", foreground="red")
                return
            folders = folders or []
            for f in folders:
                self._tree.insert("", "end", values=(f["id"], f.get("name", "")))
            self._status_label.config(
                text=f"{len(folders)} folder(s) found.", foreground="gray"
            )
            self.app.discovered_folders = folders

        _run_in_thread(fetch, done)


# ---------------------------------------------------------------------------
# Mappings Tab
# ---------------------------------------------------------------------------

class MappingsTab(ttk.Frame):
    def __init__(self, parent, app: "App"):
        super().__init__(parent, padding=16)
        self.app = app
        self._build()

    def _build(self):
        ttk.Label(self, text="Folder Mappings", font=("", 12, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            self,
            text="Map each Granola folder to a local directory where notes will be saved.",
            foreground="gray",
        ).grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 10))

        # Table
        cols = ("Folder ID", "Folder Name", "Local Path")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", height=10)
        self._tree.heading("Folder ID", text="Folder ID")
        self._tree.heading("Folder Name", text="Folder Name")
        self._tree.heading("Local Path", text="Local Path")
        self._tree.column("Folder ID", width=160)
        self._tree.column("Folder Name", width=160)
        self._tree.column("Local Path", width=260)
        self._tree.grid(row=2, column=0, columnspan=4, sticky="nsew")

        sb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.grid(row=2, column=4, sticky="ns")

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=4, sticky="w", pady=(8, 0))
        ttk.Button(btn_frame, text="Add", command=self._add).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="Edit Path", command=self._edit).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="Delete", command=self._delete).pack(side="left")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._refresh()

    def _refresh(self):
        self._tree.delete(*self._tree.get_children())
        for m in list_mappings():
            self._tree.insert(
                "", "end",
                iid=m["folder_id"],
                values=(m["folder_id"], m.get("folder_name", ""), m["local_path"]),
            )

    def _add(self):
        folders = self.app.discovered_folders
        if not folders:
            messagebox.showinfo(
                "No folders",
                "Go to the Setup tab and click 'Discover Folders' first.",
            )
            return
        AddMappingDialog(self, folders, on_save=self._refresh)

    def _edit(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Select a row", "Select a mapping to edit.")
            return
        folder_id = sel[0]
        current = get_mapping(folder_id)
        new_path = filedialog.askdirectory(
            title="Choose new local folder",
            initialdir=current["local_path"] if current else None,
        )
        if new_path:
            update_mapping(folder_id, local_path=new_path)
            self._refresh()

    def _delete(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Select a row", "Select a mapping to delete.")
            return
        folder_id = sel[0]
        if messagebox.askyesno("Delete?", f"Remove mapping for {folder_id}?"):
            delete_mapping(folder_id)
            self._refresh()


class AddMappingDialog(tk.Toplevel):
    def __init__(self, parent, folders: list[dict], on_save):
        super().__init__(parent)
        self.title("Add Mapping")
        self.resizable(False, False)
        self.grab_set()
        self._folders = folders
        self._on_save = on_save
        self._build()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Granola Folder:").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._folder_var = tk.StringVar()
        names = [f"{f.get('name', '')}  ({f['id']})" for f in self._folders]
        combo = ttk.Combobox(frame, textvariable=self._folder_var, values=names, width=40, state="readonly")
        combo.grid(row=0, column=1, sticky="ew", pady=(0, 4))
        if names:
            combo.current(0)

        ttk.Label(frame, text="Local Path:").grid(row=1, column=0, sticky="w", pady=(0, 4))
        path_frame = ttk.Frame(frame)
        path_frame.grid(row=1, column=1, sticky="ew", pady=(0, 12))
        self._path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self._path_var, width=32).pack(side="left", padx=(0, 6))
        ttk.Button(path_frame, text="Browse…", command=self._browse).pack(side="left")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="e")
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="left")

        frame.columnconfigure(1, weight=1)

    def _browse(self):
        path = filedialog.askdirectory(title="Choose local folder")
        if path:
            self._path_var.set(path)

    def _save(self):
        raw = self._folder_var.get()
        local_path = self._path_var.get().strip()
        if not raw or not local_path:
            messagebox.showwarning("Incomplete", "Please select a folder and a local path.")
            return
        # Parse "Name  (fol_xxx)" back to id + name
        idx = next(
            (i for i, f in enumerate(self._folders) if f["id"] in raw),
            None,
        )
        if idx is None:
            messagebox.showerror("Error", "Could not identify folder.")
            return
        folder = self._folders[idx]
        try:
            create_mapping(folder["id"], folder.get("name", ""), local_path)
        except ValueError as e:
            messagebox.showerror("Already exists", str(e))
            return
        self._on_save()
        self.destroy()


# ---------------------------------------------------------------------------
# Sync Tab
# ---------------------------------------------------------------------------

class SyncTab(ttk.Frame):
    def __init__(self, parent, app: "App"):
        super().__init__(parent, padding=16)
        self.app = app
        self._build()

    def _build(self):
        ttk.Label(self, text="Sync", font=("", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            self,
            text="Fetch new and updated notes from Granola and save them locally.",
            foreground="gray",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self._dry_btn = ttk.Button(btn_frame, text="Dry Run (preview)", command=self._dry_run)
        self._dry_btn.pack(side="left", padx=(0, 8))
        self._sync_btn = ttk.Button(btn_frame, text="Sync Now", command=self._sync)
        self._sync_btn.pack(side="left")

        self._status = ttk.Label(self, text="", foreground="gray")
        self._status.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self._log = tk.Text(self, width=70, height=20, state="disabled", wrap="word",
                            font=("Menlo", 11))
        self._log.grid(row=4, column=0, sticky="nsew")
        sb = ttk.Scrollbar(self, orient="vertical", command=self._log.yview)
        self._log.configure(yscrollcommand=sb.set)
        sb.grid(row=4, column=1, sticky="ns")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

    def _log_write(self, text: str):
        self._log.config(state="normal")
        self._log.insert("end", text)
        self._log.see("end")
        self._log.config(state="disabled")

    def _log_clear(self):
        self._log.config(state="normal")
        self._log.delete("1.0", "end")
        self._log.config(state="disabled")

    def _set_buttons(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self._dry_btn.config(state=state)
        self._sync_btn.config(state=state)

    def _run_sync(self, dry: bool):
        if not list_mappings():
            messagebox.showinfo("No mappings", "Add at least one folder mapping first.")
            return
        self._log_clear()
        self._set_buttons(False)
        label = "Dry run" if dry else "Sync"
        self._status.config(text=f"{label} in progress…", foreground="gray")

        def fn():
            return sync_dry_run() if dry else sync_all()

        def done(results, error):
            self._set_buttons(True)
            if error:
                self._status.config(text=f"Error: {error}", foreground="red")
                self._log_write(f"ERROR: {error}\n")
                return

            total_written = total_skipped = total_errors = 0
            for r in (results or []):
                self._log_write(f"\n📁  {r.folder_name}  →  {r.local_path}\n")
                for n in r.notes:
                    if n.status == "written":
                        prefix = "  ✅  (dry)" if dry else "  ✅ "
                        self._log_write(f"{prefix} {n.title}\n")
                    elif n.status == "skipped":
                        self._log_write(f"  –  {n.title}  (unchanged)\n")
                    else:
                        self._log_write(f"  ❌  {n.title}  ERROR: {n.error}\n")
                self._log_write(
                    f"     {r.written} written · {r.skipped} skipped · {r.errors} errors\n"
                )
                total_written += r.written
                total_skipped += r.skipped
                total_errors += r.errors

            summary = (
                f"{label} complete — "
                f"{total_written} written, {total_skipped} skipped, {total_errors} errors"
            )
            self._status.config(
                text=summary,
                foreground="red" if total_errors else "green",
            )

        _run_in_thread(fn, done)

    def _dry_run(self):
        self._run_sync(dry=True)

    def _sync(self):
        self._run_sync(dry=False)


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Granola Sync")
        self.geometry("720x560")
        self.minsize(600, 460)

        self.api_key: str | None = get_api_key()
        self.discovered_folders: list[dict] = []

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self._setup_tab = SetupTab(notebook, self)
        self._mappings_tab = MappingsTab(notebook, self)
        self._sync_tab = SyncTab(notebook, self)

        notebook.add(self._setup_tab, text="  Setup  ")
        notebook.add(self._mappings_tab, text="  Mappings  ")
        notebook.add(self._sync_tab, text="  Sync  ")

        # Refresh mappings table whenever that tab is selected
        notebook.bind(
            "<<NotebookTabChanged>>",
            lambda _: self._mappings_tab._refresh()
        )


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
