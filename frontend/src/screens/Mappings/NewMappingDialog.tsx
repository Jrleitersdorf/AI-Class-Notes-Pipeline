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
