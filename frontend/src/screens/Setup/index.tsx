import { useEffect, useState } from "react";
import { waitForBridge } from "../../api";
import { useStore } from "../../state";
import { Card, CardTitle, CardSubtitle } from "../../components/Card";
import { Button } from "../../components/Button";
import { Input } from "../../components/Input";
import { formatRelativeTime } from "../../lib/format";

export function SetupTab() {
  const { apiKey, folders, foldersRefreshedAt, setApiKey, setFolders, showToast } = useStore();
  const [keyDraft, setKeyDraft] = useState(apiKey ?? "");
  const [showKey, setShowKey] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    waitForBridge().then(async (api) => {
      const saved = await api.get_api_key();
      if (saved) {
        setApiKey(saved);
        setKeyDraft(saved);
      }
      const cache = await api.load_cached_folders();
      setFolders(cache.folders, cache.refreshed_at);
    });
  }, [setApiKey, setFolders]);

  async function save() {
    if (!keyDraft.trim()) return;
    const api = await waitForBridge();
    await api.set_api_key(keyDraft.trim());
    setApiKey(keyDraft.trim());
    showToast("info", "API key saved.");
  }

  async function refresh() {
    setRefreshing(true);
    try {
      const api = await waitForBridge();
      const cache = await api.refresh_folders();
      setFolders(cache.folders, cache.refreshed_at);
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardTitle>Granola API key</CardTitle>
        <CardSubtitle>
          Get yours from the Granola desktop app → Settings → API → Create new key.
        </CardSubtitle>
        <div className="flex gap-2">
          <Input
            type={showKey ? "text" : "password"}
            value={keyDraft}
            onChange={(e) => setKeyDraft(e.target.value)}
            placeholder="grn_..."
            autoComplete="off"
            spellCheck={false}
          />
          <Button variant="secondary" onClick={() => setShowKey((s) => !s)}>
            {showKey ? "Hide" : "Show"}
          </Button>
          <Button onClick={save} disabled={!keyDraft.trim()}>
            Save
          </Button>
        </div>
      </Card>

      <Card>
        <div className="flex items-center justify-between mb-2">
          <CardTitle className="mb-0">Discovered folders</CardTitle>
          <Button variant="ghost" onClick={refresh} disabled={refreshing}>
            {refreshing ? "Refreshing…" : "⟳ Refresh"}
          </Button>
        </div>
        <CardSubtitle>
          {folders.length} folder(s) · refreshed {formatRelativeTime(foldersRefreshedAt)}
        </CardSubtitle>
        <div className="flex flex-col gap-1 max-h-[280px] overflow-auto pr-1">
          {folders.length === 0 ? (
            <p className="text-faint text-[11px] py-2">
              No folders cached. Save your API key and click Refresh.
            </p>
          ) : (
            folders.map((f) => (
              <div
                key={f.id}
                className="bg-surface border border-border rounded-[5px] px-3 py-1.5 text-[11px]"
              >
                {f.name}
              </div>
            ))
          )}
        </div>
      </Card>
      <button
        onClick={() => useStore.getState().setWizardStep(1)}
        className="text-muted text-[11px] hover:text-[color:var(--text)] self-start"
      >
        Re-run setup wizard
      </button>
    </div>
  );
}
