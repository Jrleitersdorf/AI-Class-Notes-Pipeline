import { create } from "zustand";
import { createSetupSlice, type SetupSlice } from "./setup";
import { createMappingsSlice, type MappingsSlice } from "./mappings";
import { createSyncSlice, type SyncSlice } from "./sync";
import { createUISlice, type UISlice } from "./ui";

export type { Tab } from "./ui";

export type Store = SetupSlice & MappingsSlice & SyncSlice & UISlice;

export const useStore = create<Store>()((set) => ({
  ...createSetupSlice(set),
  ...createMappingsSlice(set),
  ...createSyncSlice(set),
  ...createUISlice(set),
}));
