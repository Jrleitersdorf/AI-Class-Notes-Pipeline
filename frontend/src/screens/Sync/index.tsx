import { useState } from "react";
import { waitForBridge, type SyncEvent } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";
import { Card, CardTitle, CardSubtitle } from "../../components/Card";

function eventLine(e: SyncEvent): { color: string; text: string } | null {
  if (e.type === "note") {
    if (e.status === "written") return { color: "text-success", text: `✓ Written: ${e.title}` };
    if (e.status === "skipped") return { color: "text-faint",   text: `○ Skipped: ${e.title}` };
    return { color: "text-error", text: `✗ Error: ${e.title} — ${e.error ?? ""}` };
  }
  if (e.type === "folder_done") {
    return {
      color: "text-muted",
      text: `— ${e.folder_name}: ${e.written} written, ${e.skipped} skipped, ${e.errors} errors`,
    };
  }
  if (e.type === "done") {
    return {
      color: "text-[color:var(--text)]",
      text: `Done — ${e.written} written, ${e.skipped} skipped, ${e.errors} errors (${(e.elapsed_ms / 1000).toFixed(1)}s)`,
    };
  }
  return { color: "text-error", text: `Sync error: ${e.message}` };
}

export function SyncTab() {
  const { running, events, syncId, startSync, clearLog, showToast } = useStore();
  const [dryRunResult, setDryRunResult] = useState<string | null>(null);

  async function dryRun() {
    try {
      const api = await waitForBridge();
      const results = await api.sync_dry_run();
      const w = results.reduce((s, r) => s + r.written, 0);
      const k = results.reduce((s, r) => s + r.skipped, 0);
      setDryRunResult(`${w} would be written, ${k} already up-to-date`);
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    }
  }

  async function runSync() {
    try {
      clearLog();
      const api = await waitForBridge();
      const id = await api.start_sync();
      startSync(id);
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    }
  }

  async function cancel() {
    if (!syncId) return;
    const api = await waitForBridge();
    await api.cancel_sync(syncId);
  }

  return (
    <div className="flex flex-col gap-4 h-full">
      <Card>
        <CardTitle>Run a sync</CardTitle>
        <CardSubtitle>
          Dry run shows what would change. Sync now fetches and writes Markdown.
        </CardSubtitle>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={dryRun} disabled={running}>
            Dry run
          </Button>
          {running ? (
            <Button variant="danger" onClick={cancel}>Cancel sync</Button>
          ) : (
            <Button onClick={runSync}>Sync now</Button>
          )}
          <Button variant="ghost" onClick={clearLog} disabled={events.length === 0}>
            Clear log
          </Button>
        </div>
        {dryRunResult && (
          <p className="text-muted text-[11px] mt-2">{dryRunResult}</p>
        )}
      </Card>

      <Card className="flex-1 flex flex-col">
        <CardTitle>Activity log</CardTitle>
        <div className="flex-1 overflow-auto font-mono text-[11px] leading-relaxed mt-2 min-h-[180px]">
          {events.length === 0 ? (
            <p className="text-faint">No activity yet.</p>
          ) : (
            events.map((e, i) => {
              const line = eventLine(e);
              if (!line) return null;
              return <div key={i} className={line.color}>{line.text}</div>;
            })
          )}
        </div>
      </Card>
    </div>
  );
}
