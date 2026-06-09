import { useState } from "react";
import { waitForBridge } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";

export function Step3Mapping() {
  const { folders, setMappings, setWizardStep, showToast } = useStore();
  const pickedId: string | null = (window as any).__wizardPickedFolderId ?? null;
  const folder = folders.find((f) => f.id === pickedId);
  const [localPath, setLocalPath] = useState<string>("");
  const [busy, setBusy] = useState(false);

  async function pickFolder() {
    const api = await waitForBridge();
    const path = await api.pick_folder(`Choose destination for ${folder?.name ?? ""}`);
    if (path) setLocalPath(path);
  }

  async function next() {
    if (!folder || !localPath) return;
    setBusy(true);
    try {
      const api = await waitForBridge();
      await api.create_mapping(folder.id, folder.name, localPath, "both");
      const refreshed = await api.list_mappings();
      setMappings(refreshed);
      setWizardStep(4);
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="text-center">
      <h2 className="text-[16px] font-semibold mb-1">
        Where should <span className="text-accent">{folder?.name ?? "this folder"}</span> go on your Mac?
      </h2>
      <p className="text-muted text-[11px] mb-5">
        Pick a local folder — Granola notes will be written there as Markdown.
      </p>

      <button
        onClick={pickFolder}
        className={`w-full mb-4 px-4 py-6 rounded-[8px] text-[12px] transition-colors
          ${localPath
            ? "bg-surface border border-[color:var(--border-accent)] text-[color:var(--text)]"
            : "bg-elevated border border-dashed border-border text-muted hover:text-[color:var(--text)]"}`}
      >
        {localPath ? localPath : "Click to choose a folder"}
      </button>

      {folder && localPath && (
        <p className="text-muted text-[11px] mb-5 font-mono">
          {folder.name} → {localPath}
        </p>
      )}

      <div className="flex gap-2 justify-center">
        <Button variant="secondary" onClick={() => setWizardStep(2)}>Back</Button>
        <Button onClick={next} disabled={busy || !localPath}>
          {busy ? "Saving…" : "Continue →"}
        </Button>
      </div>
    </div>
  );
}
