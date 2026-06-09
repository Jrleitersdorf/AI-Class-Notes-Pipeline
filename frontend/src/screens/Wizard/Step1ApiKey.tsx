import { useState } from "react";
import { waitForBridge } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";
import { Input } from "../../components/Input";

export function Step1ApiKey() {
  const { setApiKey, setWizardStep, showToast } = useStore();
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);

  async function next() {
    if (!key.trim()) return;
    setBusy(true);
    try {
      const api = await waitForBridge();
      await api.set_api_key(key.trim());
      setApiKey(key.trim());
      setWizardStep(2);
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="text-center">
      <h2 className="text-[16px] font-semibold mb-1">Paste your Granola API key</h2>
      <p className="text-muted text-[11px] mb-5">
        Granola desktop → Settings → API → Create new key.
      </p>
      <Input
        type="password"
        value={key}
        onChange={(e) => setKey(e.target.value)}
        placeholder="grn_..."
        autoFocus
        spellCheck={false}
        autoComplete="off"
        className="mb-4"
      />
      <Button onClick={next} disabled={!key.trim() || busy}>
        {busy ? "Saving…" : "Continue →"}
      </Button>
    </div>
  );
}
