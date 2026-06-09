import type { Mapping } from "../api";

export interface MappingsSlice {
  mappings: Mapping[];
  setMappings: (mappings: Mapping[]) => void;
}

export const createMappingsSlice = (set: any): MappingsSlice => ({
  mappings: [],
  setMappings: (mappings) => set({ mappings }),
});
