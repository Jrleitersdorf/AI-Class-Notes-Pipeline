import { TabStrip, TabPanels } from "./components/Tabs";
import { SetupTab } from "./screens/Setup";
import { useStore } from "./state";

export default function App() {
  const tab = useStore((s) => s.currentTab);
  return (
    <div className="min-h-screen flex flex-col">
      <TabStrip />
      <TabPanels>
        {tab === "setup" && <SetupTab />}
        {tab === "mappings" && <Placeholder name="Mappings" />}
        {tab === "sync" && <Placeholder name="Sync" />}
      </TabPanels>
    </div>
  );
}

function Placeholder({ name }: { name: string }) {
  return <p className="text-muted text-[12px]">{name} tab — coming next.</p>;
}
