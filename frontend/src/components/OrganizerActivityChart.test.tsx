import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { OrganizerActivityChart } from "./OrganizerActivityChart";

describe("OrganizerActivityChart", () => {
  it("shows a loading state before activity data loads", () => {
    renderWithQueryClient(<OrganizerActivityChart />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders activity buckets and a game filter populated from /api/games", async () => {
    renderWithQueryClient(<OrganizerActivityChart />);

    expect(await screen.findByText("Jun 1: 2")).toBeInTheDocument();
    expect(screen.getByText("Jun 8: 1")).toBeInTheDocument();

    const select = screen.getByLabelText(/game/i);
    expect(select).toHaveDisplayValue("All");
    expect(await screen.findByRole("option", { name: "PTCG" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "POCKET" })).toBeInTheDocument();
  });

  it("refetches activity filtered by the selected game", async () => {
    renderWithQueryClient(<OrganizerActivityChart />);

    const select = await screen.findByLabelText(/game/i);
    await screen.findByRole("option", { name: "PTCG" });
    fireEvent.change(select, { target: { value: "PTCG" } });

    await waitFor(() => {
      expect(screen.getByText("Jun 1: 1")).toBeInTheDocument();
    });
    expect(screen.queryByText("Jun 8: 1")).not.toBeInTheDocument();
  });
});
