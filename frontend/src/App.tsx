import { useEffect, useState } from "react";
import { waitForBridge } from "./api";

export default function App() {
  const [version, setVersion] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    waitForBridge()
      .then((api) => api.get_version())
      .then(setVersion)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div>
        <h1 className="text-2xl font-semibold">Granola Sync</h1>
        {version && <p className="text-muted text-sm mt-1">v{version}</p>}
        {error && <p className="text-error text-sm mt-1">{error}</p>}
      </div>
    </div>
  );
}
