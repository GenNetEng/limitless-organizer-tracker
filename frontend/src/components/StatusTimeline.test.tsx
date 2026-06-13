import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { StatusTimeline } from "./StatusTimeline";

describe("StatusTimeline", () => {
  it("shows a loading state before the status history loads", () => {
    renderWithQueryClient(<StatusTimeline />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders status checks ordered as returned by the API", async () => {
    renderWithQueryClient(<StatusTimeline />);

    expect(await screen.findByText("check 2")).toBeInTheDocument();
    expect(screen.getByText("check 1")).toBeInTheDocument();
    expect(screen.getByText("pending")).toBeInTheDocument();
    expect(screen.getByText("approved")).toBeInTheDocument();
  });
});
