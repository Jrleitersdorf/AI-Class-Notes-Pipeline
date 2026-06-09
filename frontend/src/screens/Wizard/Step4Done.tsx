import { useState } from "react";
import { waitForBridge } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";

export function Step4Done() {
  const { mappings, setWizardStep, setTab, startSync, clearLog, showToast } = useStore();
  const [busy, setBusy] = useState(false);

  function finish() {
    setWizardStep(null);
    setTab("mappings");
  }

  async function syncNow() {
    const first = mappings[0];
    if (!first) return finish();
    setBusy(true);
    try {
      const api = await waitForBridge();
      clearLog();
      const id = await api.start_sync(first.folder_id);
      startSync(id);
      setWizardStep(null);
      setTab("sync");
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
      setBusy(false);
    }
  }

  return (
    <div className="text-center">
      <h2 className="text-[20px] font-semibold mb-1">You're set up.</h2>
      <p className="text-muted text-[12px] mb-6">
        {mappings.length} mapping ready. Sync now or come back later.
      </p>
      <div className="flex gap-2 justify-center">
        <Button variant="secondary" onClick={finish} disabled={busy}>
          Maybe later
        </Button>
        <Button onClick={syncNow} disabled={busy || mappings.length === 0}>
          {busy ? "Starting…" : "Sync now"}
        </Button>
      </div>
    </div>
  );
}
