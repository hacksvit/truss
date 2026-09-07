import { afterEach, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import fixtures from "../../fixtures/snapshots.json";
import Evidence from "../src/console/Evidence";
import { api } from "../src/console/transport";
import type { ConsoleSnapshot, Replay } from "../src/console/types";
vi.mock("../src/console/transport", () => ({ api: vi.fn() }));
const sample = () =>
  ({
    ...structuredClone(fixtures[0].data),
    source: "live",
    capabilities: { ...fixtures[0].data.capabilities, replay: true },
  }) as unknown as ConsoleSnapshot;
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});
it("closes a late replay session when the console changes source", async () => {
  const s = sample();
  let complete!: (r: Replay) => void;
  vi.mocked(api).mockImplementation(async (_source, path, _body, options) => {
    if (path === "recordings")
      return {
        items: [
          { recorded_run_id: "recorded-run", bytes: 100, replayable: true },
        ],
      };
    if (path === "replays")
      return new Promise<Replay>((resolve) => (complete = resolve));
    if (options?.method === "DELETE") return { deleted: true };
    throw Error(path);
  });
  const { rerender } = render(
    <Evidence
      key="live"
      s={s}
      source="live"
      history={[]}
      report={null}
      stale={false}
    />,
  );
  await waitFor(() =>
    expect(
      (
        screen.getByRole("button", {
          name: "Open recording",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false),
  );
  fireEvent.click(screen.getByRole("button", { name: "Open recording" }));
  rerender(
    <Evidence
      key="mock"
      s={{ ...s, source: "mock" }}
      source="mock"
      history={[]}
      report={null}
      stale={false}
    />,
  );
  await act(async () => complete({ replay_id: "late-session" } as Replay));
  expect(screen.queryByRole("button", { name: "Play replay" })).toBeNull();
  expect(api).toHaveBeenCalledWith("live", "replays/late-session", undefined, {
    method: "DELETE",
  });
});
it("warns that disconnected evidence is last-known state", () => {
  vi.mocked(api).mockResolvedValue({ items: [] });
  render(
    <Evidence s={sample()} source="live" history={[]} report={null} stale />,
  );
  expect(
    screen.getByText(/Exports are marked as last-known state/),
  ).toBeTruthy();
});
