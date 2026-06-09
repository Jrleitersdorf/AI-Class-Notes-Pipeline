import { useEffect } from "react";
import { useStore } from "../state";

export function Toast() {
  const { toast, clearToast } = useStore();

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(clearToast, 4000);
    return () => clearTimeout(t);
  }, [toast, clearToast]);

  if (!toast) return null;
  return (
    <div
      className={`fixed bottom-4 right-4 z-50 max-w-[320px] rounded-[8px] px-3 py-2 text-[12px]
        ${toast.kind === "error"
          ? "bg-error text-white"
          : "bg-elevated border border-border text-[color:var(--text)]"}`}
      onClick={clearToast}
    >
      {toast.message}
    </div>
  );
}
