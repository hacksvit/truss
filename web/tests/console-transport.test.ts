import { afterEach, expect, it, vi } from "vitest";
import fixtures from "../../fixtures/snapshots.json";
import { ApiError, intent, sendIntent, state } from "../src/console/transport";
import type { ConsoleSnapshot } from "../src/console/types";
const s = { ...fixtures[0].data, source: "live" } as unknown as ConsoleSnapshot;
afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});
it("routes live console traffic separately and rejects another source", async () => {
  const fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ ...s, source: "mock" }),
  });
  vi.stubGlobal("fetch", fetch);
  await expect(state("live")).rejects.toThrow("Wrong or invalid data source");
  expect(fetch.mock.calls[0][0]).toBe("/console-api/v1/state?source=live");
});
it("retries an uncertain command with identical key, body and revision", async () => {
  const fetch = vi
    .fn()
    .mockRejectedValueOnce(new TypeError("Network failed"))
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        operation_id: "o",
        status: "applied",
        control_revision: 99,
      }),
    });
  vi.stubGlobal("fetch", fetch);
  const i = intent("live", s, "cap", { watts: 2200 });
  await expect(sendIntent(i)).rejects.toThrow("Network failed");
  await sendIntent(i);
  expect(fetch.mock.calls[0][1].body).toBe(fetch.mock.calls[1][1].body);
  expect(fetch.mock.calls[0][1].headers["Idempotency-Key"]).toBe(
    fetch.mock.calls[1][1].headers["Idempotency-Key"],
  );
});
it("polls a queued operation rather than resubmitting the action", async () => {
  vi.useFakeTimers();
  const fetch = vi
    .fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ operation_id: "o", status: "queued" }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ operation_id: "o", status: "applied" }),
    });
  vi.stubGlobal("fetch", fetch);
  const i = intent("live", s, "chaos", {
    action: "kill_coordinator",
    member_id: null,
  });
  const done = sendIntent(i);
  await vi.advanceTimersByTimeAsync(350);
  await done;
  expect(fetch.mock.calls[1][0]).toBe("/console-api/v1/operations/o");
  expect(fetch.mock.calls[1][1].method).toBe("GET");
});
it("surfaces a conflicting control revision without replacing its intent", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ error: { message: "revision_conflict" } }),
    }),
  );
  const i = intent("live", s, "cap", { watts: 2000 });
  await expect(sendIntent(i)).rejects.toBeInstanceOf(ApiError);
  expect(i.body.expected_control_revision).toBe(s.control_revision);
});
