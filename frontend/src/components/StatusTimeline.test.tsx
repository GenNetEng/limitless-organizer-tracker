import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { StatusTimeline } from "./StatusTimeline";

describe("StatusTimeline", () => {
  it("shows a loading state before the status history loads", () => {
    renderWithQueryClient(<StatusTimeline />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders status checks with capitalized status and no raw_text", async () => {
    renderWithQueryClient(<StatusTimeline />);

    expect(await screen.findByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Approved")).toBeInTheDocument();
    expect(screen.queryByText("check 1")).not.toBeInTheDocument();
    expect(screen.queryByText("check 2")).not.toBeInTheDocument();
  });

  it("displays review_note when present and omits it when null", async () => {
    renderWithQueryClient(<StatusTimeline />);

    expect(
      await screen.findByText("Your application was rejected. Please join the Discord.")
    ).toBeInTheDocument();
    // Pending and Approved items have null review_note — no note text visible
    expect(screen.queryByText("check 2")).not.toBeInTheDocument();
  });

  it("renders 'Rejected' label with red color class", async () => {
    renderWithQueryClient(<StatusTimeline />);

    const label = await screen.findByText("Rejected");
    expect(label).toHaveClass("text-red-600");
  });
});
