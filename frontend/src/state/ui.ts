export type Tab = "setup" | "mappings" | "sync";

export interface UISlice {
  currentTab: Tab;
  wizardStep: 1 | 2 | 3 | 4 | null;
  toast: { kind: "error" | "info"; message: string } | null;
  setTab: (tab: Tab) => void;
  setWizardStep: (step: 1 | 2 | 3 | 4 | null) => void;
  showToast: (kind: "error" | "info", message: string) => void;
  clearToast: () => void;
}

export const createUISlice = (set: any): UISlice => ({
  currentTab: "setup",
  wizardStep: null,
  toast: null,
  setTab: (currentTab) => set({ currentTab }),
  setWizardStep: (wizardStep) => set({ wizardStep }),
  showToast: (kind, message) => set({ toast: { kind, message } }),
  clearToast: () => set({ toast: null }),
});
