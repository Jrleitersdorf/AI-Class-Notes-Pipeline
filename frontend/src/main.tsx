import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { useStore } from "./state";
import type { SyncEvent } from "./api";
import "./theme.css";

window.granolaSync = {
  onSyncProgress(event: SyncEvent) {
    useStore.getState().appendEvent(event);
    if (event.type === "done" || event.type === "error") {
      useStore.getState().endSync();
    }
  },
};

async function bootstrap() {
  try {
    const { waitForBridge } = await import("./api");
    const api = await waitForBridge();
    const saved = await api.get_api_key();
    if (!saved) {
      useStore.getState().setWizardStep(1);
    }
  } catch {
    // Bridge unavailable in tests — leave wizard closed.
  }
}
bootstrap();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
