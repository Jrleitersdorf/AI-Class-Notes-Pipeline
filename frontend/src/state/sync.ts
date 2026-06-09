import type { SyncEvent } from "../api";

export interface SyncSlice {
  syncId: string | null;
  running: boolean;
  events: SyncEvent[];
  startSync: (id: string) => void;
  appendEvent: (event: SyncEvent) => void;
  endSync: () => void;
  clearLog: () => void;
}

export const createSyncSlice = (set: any): SyncSlice => ({
  syncId: null,
  running: false,
  events: [],
  startSync: (id) => set({ syncId: id, running: true, events: [] }),
  appendEvent: (event) =>
    set((s: any) => ({ events: [...s.events, event].slice(-500) })),
  endSync: () => set({ running: false, syncId: null }),
  clearLog: () => set({ events: [] }),
});
