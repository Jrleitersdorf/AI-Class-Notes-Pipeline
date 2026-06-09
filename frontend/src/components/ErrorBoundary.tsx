import { Component, type ReactNode } from "react";

export class ErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6">
          <div className="max-w-[420px] text-center">
            <h1 className="text-[16px] font-semibold mb-2">Something broke.</h1>
            <pre className="text-[11px] text-error font-mono bg-surface border border-border rounded p-3 overflow-auto mb-4">
              {this.state.error.message}
            </pre>
            <button
              onClick={() => location.reload()}
              className="px-3 py-1.5 bg-accent text-white rounded-md text-[12px]"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
