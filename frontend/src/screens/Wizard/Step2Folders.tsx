import { useEffect, useState } from "react";
import { waitForBridge } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";

export function Step2Folders() {
  const { folders, setFolders, setWizardStep, showToast } = useStore();
  const [pickedId, setPickedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const api = await waitForBridge();
        const cache = await api.refresh_folders();
        setFolders(cache.folders, cache.refreshed_at);
      } catch (e: any) {
        showToast("error", String(e?.message ?? e));
      } finally {
        setLoading(false);
      }
    })();
  }, [setFolders, showToast]);

  function next() {
    if (!pickedId) return;
    // Stash the picked folder for Step 3 via a global cache (avoids adding a
    // separate slice). Step 3 reads `__wizardPickedFolderId`. Write it
    // synchronously here — an effect would not fire because this component
    // unmounts in the same commit as `setWizardStep(3)`.
    (window as any).__wizardPickedFolderId = pickedId;
    setWizardStep(3);
  }

  return (
    <div className="text-center">
      <h2 className="text-[16px] font-semibold mb-1">
        {loading ? "Discovering folders…" : `Found ${folders.length} folders`}
      </h2>
      <p className="text-muted text-[11px] mb-5">
        Pick one to start with — you can map the rest later.
      </p>

      <div className="flex flex-col gap-1.5 mb-5 max-h-[180px] overflow-auto pr-1">
        {loading ? (
          <p className="text-faint text-[11px] py-3">This can take ~30 s.</p>
        ) : folders.length === 0 ? (
          <p className="text-faint text-[11px] py-3">No folders found.</p>
        ) : (
          folders.map((f) => (
            <button
              key={f.id}
              onClick={() => setPickedId(f.id)}
              className={`text-left bg-surface border rounded-[5px] px-3 py-1.5 text-[11px] transition-colors
                ${pickedId === f.id
                  ? "border-[color:var(--border-accent)] text-[color:var(--text)]"
                  : "border-border text-muted hover:text-[color:var(--text)]"}`}
            >
              {f.name}
            </button>
          ))
        )}
      </div>

      <div className="flex gap-2 justify-center">
        <Button variant="secondary" onClick={() => setWizardStep(1)}>Back</Button>
        <Button onClick={next} disabled={!pickedId}>Continue →</Button>
      </div>
    </div>
  );
}
