import { useStore } from "../../state";
import { Step1ApiKey } from "./Step1ApiKey";
import { Step2Folders } from "./Step2Folders";
import { Step3Mapping } from "./Step3Mapping";
import { Step4Done } from "./Step4Done";

export function Wizard() {
  const step = useStore((s) => s.wizardStep);
  if (step === null) return null;

  return (
    <div className="fixed inset-0 bg-bg flex flex-col items-center justify-center p-6 z-30">
      <div className="flex gap-1.5 mb-6">
        {[1, 2, 3, 4].map((n) => (
          <span
            key={n}
            className={`w-6 h-[3px] rounded-full ${
              n <= step ? "bg-accent" : "bg-border"
            }`}
          />
        ))}
      </div>

      <p className="text-[10px] uppercase tracking-wider text-accent font-semibold mb-3">
        Step {step} of 4 ·{" "}
        {step === 1 ? "Connect" : step === 2 ? "Discover" : step === 3 ? "Map" : "Ready"}
      </p>

      <div className="w-full max-w-[340px]">
        {step === 1 && <Step1ApiKey />}
        {step === 2 && <Step2Folders />}
        {step === 3 && <Step3Mapping />}
        {step === 4 && <Step4Done />}
      </div>
    </div>
  );
}
