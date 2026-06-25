import { screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
import { RecentlyOnboarded } from "./RecentlyOnboarded";

describe("RecentlyOnboarded", () => {
  it("shows a loading state before data loads", () => {
    renderWithQueryClient(<RecentlyOnboarded />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders a table of recently onboarded organizers", async () => {
    renderWithQueryClient(<RecentlyOnboarded />);

    expect(await screen.findByText("2720")).toBeInTheDocument();
    expect(screen.getByText("2719")).toBeInTheDocument();
    expect(screen.getByText("2718")).toBeInTheDocument();
  });

  it("shows detected_at timestamps", async () => {
    renderWithQueryClient(<RecentlyOnboarded />);

    await screen.findByText("2720");
    const cells = screen.getAllByRole("cell");
    const detectedAtCells = cells.filter((cell) =>
      cell.textContent?.includes("6/20/2026"),
    );
    expect(detectedAtCells.length).toBeGreaterThan(0);
  });

  it("shows first_tournament_date when available and a dash when not", async () => {
    renderWithQueryClient(<RecentlyOnboarded />);

    await screen.findByText("2720");
    expect(screen.getByText("Jun 25")).toBeInTheDocument();
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBe(2);
  });

  it("renders organizer IDs as clickable links", async () => {
    renderWithQueryClient(<RecentlyOnboarded />);

    const link = await screen.findByRole("link", { name: "2720" });
    expect(link).toHaveAttribute(
      "href",
      "https://play.limitlesstcg.com/organizer/2720",
    );
  });

  it("shows an error message on failure", async () => {
    server.use(
      http.get("*/api/organizers/recently-onboarded", () =>
        HttpResponse.json({ detail: "server error" }, { status: 500 }),
      ),
    );

    renderWithQueryClient(<RecentlyOnboarded />);

    expect(
      await screen.findByText(/failed to load/i),
    ).toBeInTheDocument();
  });

  it("shows a message when no organizers have been onboarded", async () => {
    server.use(
      http.get("*/api/organizers/recently-onboarded", () =>
        HttpResponse.json([]),
      ),
    );

    renderWithQueryClient(<RecentlyOnboarded />);

    expect(
      await screen.findByText(/no recently onboarded/i),
    ).toBeInTheDocument();
  });
});
