import { useEffect, useRef, useState } from "react";
import { waitForBridge, type Mapping } from "../../api";
import { useStore } from "../../state";
import { Button } from "../../components/Button";

const OPTIONS: { value: Mapping["extract"]; label: string }[] = [
  { value: "both",       label: "Both (notes + transcript)" },
  { value: "ai_notes",   label: "AI notes only" },
  { value: "transcript", label: "Transcript only" },
];

export function ConfigPopover({
  mapping,
  onClose,
}: {
  mapping: Mapping;
  onClose: () => void;
}) {
  const { setMappings, showToast } = useStore();
  const [extract, setExtract] = useState(mapping.extract);
  const [busy, setBusy] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [onClose]);

  async function save(newValue: Mapping["extract"]) {
    setExtract(newValue);
    setBusy(true);
    try {
      const api = await waitForBridge();
      await api.update_mapping(mapping.folder_id, { extract: newValue });
      const refreshed = await api.list_mappings();
      setMappings(refreshed);
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!confirm(`Delete mapping for ${mapping.folder_name}?`)) return;
    setBusy(true);
    try {
      const api = await waitForBridge();
      await api.delete_mapping(mapping.folder_id);
      const refreshed = await api.list_mappings();
      setMappings(refreshed);
      onClose();
    } catch (e: any) {
      showToast("error", String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      ref={ref}
      className="absolute right-0 top-full mt-1 w-[260px] bg-elevated border border-border rounded-[8px] p-3 z-10 shadow-xl"
    >
      <p className="text-[10px] uppercase tracking-wider text-faint font-semibold mb-2">
        Extract
      </p>
      <div className="flex flex-col gap-1 mb-3">
        {OPTIONS.map((opt) => (
          <label
            key={opt.value}
            className={`flex items-center gap-2 text-[12px] cursor-pointer
              ${extract === opt.value ? "text-[color:var(--text)]" : "text-muted"}`}
          >
            <input
              type="radio"
              name={`extract-${mapping.folder_id}`}
              checked={extract === opt.value}
              onChange={() => save(opt.value)}
              disabled={busy}
              className="accent-[color:var(--accent)]"
            />
            {opt.label}
          </label>
        ))}
      </div>
      <div className="border-t border-border pt-2">
        <Button variant="danger" onClick={remove} disabled={busy} className="w-full">
          Delete mapping
        </Button>
      </div>
    </div>
  );
}
