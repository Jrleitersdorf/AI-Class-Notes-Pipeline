import { describe, it, expect, beforeEach } from "vitest";
import { useStore } from "./index";

describe("useStore", () => {
  beforeEach(() => {
    // Reset store between tests
    useStore.setState({
      apiKey: null, folders: [], foldersRefreshedAt: null,
      mappings: [],
      syncId: null, running: false, events: [],
      currentTab: "setup", wizardStep: null, toast: null,
    });
  });

  it("setApiKey updates the slice", () => {
    useStore.getState().setApiKey("grn_x");
    expect(useStore.getState().apiKey).toBe("grn_x");
  });

  it("appendEvent caps log at 500 entries", () => {
    const { appendEvent } = useStore.getState();
    for (let i = 0; i < 510; i++) {
      appendEvent({ type: "note", sync_id: "x", folder_id: "f", status: "written",
                    note_id: `n${i}`, title: `T${i}` });
    }
    expect(useStore.getState().events.length).toBe(500);
  });

  it("endSync clears syncId and running", () => {
    const { startSync, endSync } = useStore.getState();
    startSync("abc");
    expect(useStore.getState().running).toBe(true);
    endSync();
    expect(useStore.getState().syncId).toBe(null);
    expect(useStore.getState().running).toBe(false);
  });

  it("setWizardStep advances", () => {
    useStore.getState().setWizardStep(2);
    expect(useStore.getState().wizardStep).toBe(2);
  });
});
