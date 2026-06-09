import { TabStrip, TabPanels } from "./components/Tabs";
import { SetupTab } from "./screens/Setup";
import { MappingsTab } from "./screens/Mappings";
import { SyncTab } from "./screens/Sync";
import { useStore } from "./state";

export default function App() {
  const tab = useStore((s) => s.currentTab);
  return (
    <div className="min-h-screen flex flex-col">
      <TabStrip />
      <TabPanels>
        {tab === "setup" && <SetupTab />}
        {tab === "mappings" && <MappingsTab />}
        {tab === "sync" && <SyncTab />}
      </TabPanels>
    </div>
  );
}
