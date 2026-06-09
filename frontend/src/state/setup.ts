import type { Folder } from "../api";

export interface SetupSlice {
  apiKey: string | null;
  folders: Folder[];
  foldersRefreshedAt: string | null;
  setApiKey: (key: string | null) => void;
  setFolders: (folders: Folder[], refreshedAt: string | null) => void;
}

export const createSetupSlice = (set: any): SetupSlice => ({
  apiKey: null,
  folders: [],
  foldersRefreshedAt: null,
  setApiKey: (apiKey) => set({ apiKey }),
  setFolders: (folders, foldersRefreshedAt) => set({ folders, foldersRefreshedAt }),
});
