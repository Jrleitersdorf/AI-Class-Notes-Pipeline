import { test, expect } from "@playwright/test";

// We inject a mock pywebview.api before the React app boots.
const MOCK_BRIDGE = `
  window.pywebview = {
    api: {
      get_version: () => Promise.resolve("2.1.0"),
      get_api_key: () => Promise.resolve(null),
      set_api_key: (k) => Promise.resolve(),
      load_cached_folders: () => Promise.resolve({ folders: [], refreshed_at: null }),
      refresh_folders: () => Promise.resolve({
        folders: [
          { id: "fol_cs101", object: "folder", name: "CS101 Lectures" },
          { id: "fol_algo",  object: "folder", name: "Algorithms" },
        ],
        refreshed_at: new Date().toISOString(),
      }),
      list_mappings: () => Promise.resolve([]),
      create_mapping: (folder_id, folder_name, local_path, extract) =>
        Promise.resolve({ folder_id, folder_name, local_path, extract }),
      pick_folder: () => Promise.resolve("/tmp/CS101"),
      sync_dry_run: () => Promise.resolve([]),
      start_sync: () => Promise.resolve("sync-id"),
      cancel_sync: () => Promise.resolve(true),
      update_mapping: () => Promise.resolve({}),
      delete_mapping: () => Promise.resolve(true),
    },
  };
`;

test("wizard happy path: key → folder → mapping → done", async ({ page }) => {
  await page.addInitScript(MOCK_BRIDGE);
  await page.goto("/");

  // Step 1: API key
  await expect(page.getByText(/Paste your Granola API key/i)).toBeVisible();
  // The Setup tab (behind the wizard overlay) also has a password input;
  // the wizard's input renders last in the DOM, so target .last().
  await page.locator('input[type="password"]').last().fill("grn_e2e");
  await page.getByRole("button", { name: /continue/i }).click();

  // Step 2: Folders
  await expect(page.getByText(/Found 2 folders/i)).toBeVisible({ timeout: 5000 });
  await page.getByRole("button", { name: "CS101 Lectures" }).click();
  await page.getByRole("button", { name: /continue/i }).click();

  // Step 3: Pick folder
  await page.getByText(/Click to choose a folder/i).click();
  await expect(page.getByRole("button", { name: "/tmp/CS101" })).toBeVisible();
  await page.getByRole("button", { name: /continue/i }).click();

  // Step 4: Done
  await expect(page.getByText(/You're set up/i)).toBeVisible();
  await page.getByRole("button", { name: /maybe later/i }).click();

  // Wizard dismissed → Mappings tab is active
  await expect(page.getByRole("button", { name: /Mappings/i })).toBeVisible();
});
