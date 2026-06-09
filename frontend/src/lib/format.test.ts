import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { formatRelativeTime } from "./format";

describe("formatRelativeTime", () => {
  beforeEach(() => { vi.useFakeTimers(); vi.setSystemTime(new Date("2026-06-03T12:00:00Z")); });
  afterEach(() => { vi.useRealTimers(); });

  it("returns 'never' for null", () => {
    expect(formatRelativeTime(null)).toBe("never");
  });

  it("returns 'just now' under a minute", () => {
    expect(formatRelativeTime("2026-06-03T11:59:30Z")).toBe("just now");
  });

  it("returns '5 min ago'", () => {
    expect(formatRelativeTime("2026-06-03T11:55:00Z")).toBe("5 min ago");
  });

  it("returns '2 hr ago'", () => {
    expect(formatRelativeTime("2026-06-03T10:00:00Z")).toBe("2 hr ago");
  });

  it("returns '1 day ago' singular", () => {
    expect(formatRelativeTime("2026-06-02T12:00:00Z")).toBe("1 day ago");
  });

  it("returns 'N days ago' plural", () => {
    expect(formatRelativeTime("2026-05-30T12:00:00Z")).toBe("4 days ago");
  });

  it("falls back to the raw string when unparseable", () => {
    expect(formatRelativeTime("not a date")).toBe("not a date");
  });
});
