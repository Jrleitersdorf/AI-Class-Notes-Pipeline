import type { ReactNode } from "react";
import { cn } from "../lib/cn";
import { useStore, type Tab } from "../state";

const TABS: { id: Tab; label: string }[] = [
  { id: "setup", label: "Setup" },
  { id: "mappings", label: "Mappings" },
  { id: "sync", label: "Sync" },
];

export function TabStrip() {
  const { currentTab, setTab } = useStore();
  return (
    <div className="flex border-b border-border px-3.5">
      {TABS.map((t) => (
        <button
          key={t.id}
          onClick={() => setTab(t.id)}
          className={cn(
            "px-3 py-2.5 text-[12px] transition-colors",
            currentTab === t.id
              ? "text-[color:var(--text)] border-b-[1.5px] border-accent font-medium"
              : "text-[color:var(--text-muted)] hover:text-[color:var(--text)]"
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function TabPanels({ children }: { children: ReactNode }) {
  return <div className="flex-1 overflow-auto p-4">{children}</div>;
}
