import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
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

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
