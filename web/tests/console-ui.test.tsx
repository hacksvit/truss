import { afterEach, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import fixtures from "../../fixtures/snapshots.json";
import { Baselines, Homes, FairnessPanel } from "../src/console/panels";
import type { ConsoleSnapshot } from "../src/console/types";
const sample = () =>
  ({
    ...structuredClone(fixtures[0].data),
    source: "live",
  }) as unknown as ConsoleSnapshot;
afterEach(cleanup);
it("hides last-known draw and lease estimates when the stream is stale", () => {
  const s = sample();
  s.members = [s.members[0]];
  render(<Homes s={s} stale onSelect={() => {}} />);
  expect(screen.getAllByText("Unknown").length).toBe(2);
  expect(screen.getByText(/Silence does not release/)).toBeTruthy();
  expect(screen.queryByText(/~[0-9]/)).toBeNull();
});
it("requires a reason and a valid baseline before enabling a review export", () => {
  const s = sample();
  render(<Baselines s={s} />);
  const button = screen.getByRole("button", {
    name: "Download unreviewed proposal",
    hidden: true,
  }) as HTMLButtonElement;
  expect(button.disabled).toBe(true);
  fireEvent.change(
    screen.getByPlaceholderText("Explain the additional fixed requirement"),
    { target: { value: "An additional fixed lighting requirement" } },
  );
  expect(button.disabled).toBe(false);
  fireEvent.change(screen.getByLabelText("Proposed minimum (W)"), {
    target: { value: "0" },
  });
  expect(button.disabled).toBe(true);
});
it("runs a labelled comparison without enabling mock policy mutation", () => {
  const s = sample();
  s.source = "mock";
  render(
    <FairnessPanel
      s={s}
      fairness={null}
      disabled={false}
      onRule={() => {
        throw Error("Must not submit");
      }}
    />,
  );
  expect(
    (screen.getByLabelText("Desired live rule") as HTMLSelectElement).disabled,
  ).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Compare policies" }));
  expect(screen.getByText("Six-minute policy illustration")).toBeTruthy();
  expect(
    screen.getByText(/This idealised model applies allocations immediately/),
  ).toBeTruthy();
});
