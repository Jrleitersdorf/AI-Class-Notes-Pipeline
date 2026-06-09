import { useEffect, useState } from "react";
import { waitForBridge, type Mapping } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";
import { NewMappingDialog } from "./NewMappingDialog";
import { ConfigPopover } from "./ConfigPopover";

const EXTRACT_LABELS: Record<Mapping["extract"], string> = {
  both: "Both",
  ai_notes: "AI notes only",
  transcript: "Transcript only",
};

export function MappingsTab() {
  const { folders, mappings, setMappings, showToast } = useStore();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [openConfig, setOpenConfig] = useState<string | null>(null);

  useEffect(() => {
    waitForBridge()
      .then((api) => api.list_mappings())
      .then(setMappings)
      .catch((e) => showToast("error", String(e?.message ?? e)));
  }, [setMappings, showToast]);

  const mappedFolderIds = new Set(mappings.map((m) => m.folder_id));

  return (
    <div className="flex gap-4 h-full">
      {/* Left pane: Granola folders */}
      <div className="flex-1 flex flex-col gap-1.5">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] uppercase tracking-wider text-faint font-semibold">
            Granola · {folders.length} folders
          </span>
        </div>
        {folders.length === 0 ? (
          <p className="text-faint text-[11px]">
            No folders cached. Refresh on the Setup tab.
          </p>
        ) : (
          folders.map((f) => {
            const isMapped = mappedFolderIds.has(f.id);
            return (
              <div
                key={f.id}
                className={`bg-surface border rounded-[6px] px-3 py-2 text-[11px] flex items-center gap-2
                  ${isMapped ? "border-[color:var(--border-accent)]" : "border-border text-faint"}`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${isMapped ? "bg-accent" : "bg-border"}`}
                />
                {f.name}
              </div>
            );
          })
        )}
      </div>

      {/* Arrows column */}
      <div className="w-6 flex flex-col pt-7 gap-1.5 items-center text-accent text-[12px]">
        {mappings.map((m) => (
          <div key={m.folder_id} className="h-7 flex items-center">→</div>
        ))}
      </div>

      {/* Right pane: Local destinations */}
      <div className="flex-1 flex flex-col gap-1.5">
        <span className="text-[10px] uppercase tracking-wider text-faint font-semibold mb-1.5">
          Local · {mappings.length} mapped
        </span>
        {mappings.map((m) => (
          <div
            key={m.folder_id}
            className="bg-surface border border-[color:var(--border-accent)] rounded-[6px] px-3 py-2 text-[11px] flex items-center gap-2 relative"
          >
            <div className="flex-1 flex flex-col">
              <span>{m.local_path}</span>
              <span className="text-[9px] text-faint">{EXTRACT_LABELS[m.extract]}</span>
            </div>
            <button
              className="text-faint hover:text-[color:var(--text)] text-[11px]"
              onClick={() => setOpenConfig(openConfig === m.folder_id ? null : m.folder_id)}
              aria-label="Configure mapping"
            >
              ⚙
            </button>
            {openConfig === m.folder_id && (
              <ConfigPopover
                mapping={m}
                onClose={() => setOpenConfig(null)}
              />
            )}
          </div>
        ))}
        <Button
          variant="secondary"
          className="mt-1.5 border-dashed text-faint"
          onClick={() => setDialogOpen(true)}
        >
          + New mapping
        </Button>
      </div>

      {dialogOpen && <NewMappingDialog onClose={() => setDialogOpen(false)} />}
    </div>
  );
}
