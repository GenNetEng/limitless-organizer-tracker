import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
import { ScannerStatusCard } from "./ScannerStatusCard";

describe("ScannerStatusCard", () => {
  it("shows loading state initially", () => {
    renderWithQueryClient(<ScannerStatusCard />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders scanner watermark (highest organizer ID)", async () => {
    renderWithQueryClient(<ScannerStatusCard />);
    expect(await screen.findByText("2720")).toBeInTheDocument();
    expect(screen.getByText(/watermark/i)).toBeInTheDocument();
  });

  it("renders last scan time from audit_complete event", async () => {
    server.use(
      http.get("*/api/admin/event-log", ({ request }) => {
        const url = new URL(request.url);
        const eventType = url.searchParams.get("event_type");
        if (eventType === "scanner.audit_complete") {
          return HttpResponse.json({
            items: [
              {
                id: 10,
                timestamp: "2026-06-25T14:00:00Z",
                event_type: "scanner.audit_complete",
                severity: "info",
                source: "organizer_tasks",
                message: "Organizer audit: queued 3 scan tasks (IDs 2721–2723)",
                details: { start_id: 2721, queued: 3 },
                correlation_id: null,
              },
            ],
            total: 1,
            limit: 1,
            offset: 0,
          });
        }
        return HttpResponse.json({ items: [], total: 0, limit: 50, offset: 0 });
      }),
    );
    renderWithQueryClient(<ScannerStatusCard />);
    expect(await screen.findByText("3")).toBeInTheDocument();
    expect(screen.getByText("Last Scan")).toBeInTheDocument();
  });

  it("renders organizers found in last scan", async () => {
    server.use(
      http.get("*/api/admin/event-log", ({ request }) => {
        const url = new URL(request.url);
        const eventType = url.searchParams.get("event_type");
        if (eventType === "scanner.audit_complete") {
          return HttpResponse.json({
            items: [
              {
                id: 10,
                timestamp: "2026-06-25T14:00:00Z",
                event_type: "scanner.audit_complete",
                severity: "info",
                source: "organizer_tasks",
                message: "Organizer audit: queued 3 scan tasks (IDs 2721–2723)",
                details: { start_id: 2721, queued: 3 },
                correlation_id: null,
              },
            ],
            total: 1,
            limit: 1,
            offset: 0,
          });
        }
        return HttpResponse.json({ items: [], total: 0, limit: 50, offset: 0 });
      }),
    );
    renderWithQueryClient(<ScannerStatusCard />);
    expect(await screen.findByText("3")).toBeInTheDocument();
    expect(screen.getByText(/found in last scan/i)).toBeInTheDocument();
  });

  it("shows no scan data message when no audit events exist", async () => {
    server.use(
      http.get("*/api/admin/event-log", () =>
        HttpResponse.json({ items: [], total: 0, limit: 1, offset: 0 }),
      ),
    );
    renderWithQueryClient(<ScannerStatusCard />);
    const noDataElements = await screen.findAllByText(/no scan data/i);
    expect(noDataElements.length).toBeGreaterThanOrEqual(1);
  });

  it("shows friendly message when highest-id returns 404", async () => {
    server.use(
      http.get("*/api/organizers/highest-id", () =>
        HttpResponse.json({ detail: "no organizer data available" }, { status: 404 }),
      ),
    );
    renderWithQueryClient(<ScannerStatusCard />);
    expect(await screen.findByText(/no organizer data/i)).toBeInTheDocument();
  });

  it("shows error state on API failure", async () => {
    server.use(
      http.get("*/api/organizers/highest-id", () =>
        HttpResponse.json({ detail: "server error" }, { status: 500 }),
      ),
    );
    renderWithQueryClient(<ScannerStatusCard />);
    expect(await screen.findByText(/failed to load/i)).toBeInTheDocument();
  });
});
