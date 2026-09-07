import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import fixtures from "../../fixtures/snapshots.json";
import Console from "../src/routes/Console";
import { useConsole } from "../src/console/useConsole";
import type { ConsoleSnapshot } from "../src/console/types";
vi.mock("../src/console/useConsole", () => ({ useConsole: vi.fn() }));
vi.mock("recharts", () => ({
  ResponsiveContainer: () => null,
  LineChart: () => null,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  CartesianGrid: () => null,
  Legend: () => null,
}));
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
it("keeps one minimum review and one evidence section across snapshot and run changes", () => {
  const errors = vi.spyOn(console, "error");
  const s = structuredClone(fixtures[0].data) as unknown as ConsoleSnapshot;
  const value = {
    source: "mock" as const,
    setSource: vi.fn(),
    snapshot: s,
    connection: "connected" as const,
    history: [],
    runtime: null,
    fairness: null,
    auxError: "",
    busy: false,
    setBusy: vi.fn(),
    message: "",
    setMessage: vi.fn(),
    operation: null,
    unresolved: null,
    act: vi.fn(),
    retry: vi.fn(),
  };
  vi.mocked(useConsole).mockReturnValue(value);
  const { rerender, container } = render(<Console />);
  for (let i = 1; i <= 12; i++) {
    vi.mocked(useConsole).mockReturnValue({
      ...value,
      snapshot: { ...s, revision: i, run_id: i < 6 ? s.run_id : "new-run" },
    });
    rerender(<Console />);
    expect(container.querySelectorAll("#baselines")).toHaveLength(1);
    expect(container.querySelectorAll("#evidence")).toHaveLength(1);
  }
  expect(screen.getByText("Minimums require a decision.")).toBeTruthy();
  expect(
    errors.mock.calls.some((call) =>
      call.some((v) => String(v).includes("same key")),
    ),
  ).toBe(false);
});
