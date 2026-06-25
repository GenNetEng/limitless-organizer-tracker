import { fireEvent, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
import { EventLogViewer } from "./EventLogViewer";

describe("EventLogViewer", () => {
  it("renders event log entries from the API", async () => {
    renderWithQueryClient(<EventLogViewer />);

    expect(await screen.findByText("ingest_tournaments completed")).toBeInTheDocument();
    expect(screen.getByText("ingest_tournaments started")).toBeInTheDocument();
    expect(screen.getByText("Resubmit button not found")).toBeInTheDocument();
  });

  it("displays severity badges for each entry", async () => {
    renderWithQueryClient(<EventLogViewer />);

    await screen.findByText("ingest_tournaments completed");

    const infoBadges = screen.getAllByText("info");
    expect(infoBadges.length).toBe(2);
    expect(screen.getByText("error")).toBeInTheDocument();
  });

  it("displays event type and source for each entry", async () => {
    renderWithQueryClient(<EventLogViewer />);

    await screen.findByText("ingest_tournaments completed");

    expect(screen.getAllByText("celery").length).toBe(2);
    expect(screen.getByText("resubmit")).toBeInTheDocument();
    expect(screen.getByText("task.completed")).toBeInTheDocument();
    expect(screen.getByText("scraper.error")).toBeInTheDocument();
  });

  it("shows a loading state while fetching", () => {
    renderWithQueryClient(<EventLogViewer />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows error message on API failure", async () => {
    server.use(
      http.get("*/api/admin/event-log", () => HttpResponse.json(null, { status: 500 })),
    );
    renderWithQueryClient(<EventLogViewer />);
    expect(await screen.findByText("Failed to load event log")).toBeInTheDocument();
  });

  it("shows pagination controls when total exceeds page size", async () => {
    const items = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      timestamp: `2026-06-22T${String(i % 24).padStart(2, "0")}:00:00Z`,
      event_type: "task.completed",
      severity: "info",
      source: "celery",
      message: `event ${i + 1}`,
      details: null,
      correlation_id: null,
    }));

    server.use(
      http.get("*/api/admin/event-log", ({ request }) => {
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

    renderWithQueryClient(<EventLogViewer />);

    expect(await screen.findByText(/page 1 of 2/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /previous/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /next/i })).not.toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    expect(await screen.findByText(/page 2 of 2/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /next/i })).toBeDisabled();
  });

  it("does not show pagination when all items fit on one page", async () => {
    renderWithQueryClient(<EventLogViewer />);

    await screen.findByText("ingest_tournaments completed");
    expect(screen.queryByRole("button", { name: /next/i })).not.toBeInTheDocument();
  });
});
