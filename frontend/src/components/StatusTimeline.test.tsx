import { fireEvent, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
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

  it("renders 'Rejected' label with error badge", async () => {
    renderWithQueryClient(<StatusTimeline />);

    const label = await screen.findByText("Rejected");
    expect(label).toHaveClass("badge-error");
  });

  it("shows pagination controls when total exceeds page size", async () => {
    const items = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      checked_at: `2026-06-${String(12 + Math.floor(i / 10)).padStart(2, "0")}T${String(i % 24).padStart(2, "0")}:00:00Z`,
      status: "pending",
      raw_text: null,
      review_note: null,
    }));

    server.use(
      http.get("*/api/status-history", ({ request }) => {
        const url = new URL(request.url);
        const limit = Number(url.searchParams.get("limit") ?? 20);
        const offset = Number(url.searchParams.get("offset") ?? 0);
        return HttpResponse.json({
          items: items.slice(offset, offset + limit),
          total: items.length,
          limit,
          offset,
        });
      }),
    );

    renderWithQueryClient(<StatusTimeline />);

    expect(await screen.findByText(/page 1 of 2/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /previous/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /next/i })).not.toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    expect(await screen.findByText(/page 2 of 2/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /next/i })).toBeDisabled();
  });

  it("does not show pagination when all items fit on one page", async () => {
    renderWithQueryClient(<StatusTimeline />);

    await screen.findByText("Pending");
    expect(screen.queryByText(/page/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /next/i })).not.toBeInTheDocument();
  });

  it("shows error message on API failure", async () => {
    server.use(
      http.get("*/api/status-history", () => HttpResponse.json(null, { status: 500 })),
    );
    renderWithQueryClient(<StatusTimeline />);
    expect(await screen.findByText("Failed to load status history")).toBeInTheDocument();
  });
});
