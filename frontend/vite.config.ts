import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  // Use relative paths so the bundle works when loaded from file:// inside pywebview
  base: "./",
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: { port: 5173, strictPort: true },
  build: { outDir: "dist", assetsDir: "assets" },
});
