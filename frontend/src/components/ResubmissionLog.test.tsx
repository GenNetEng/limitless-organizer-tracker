import { fireEvent, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
import { ResubmissionLog } from "./ResubmissionLog";

describe("ResubmissionLog", () => {
  it("shows a loading state before the resubmission log loads", () => {
    renderWithQueryClient(<ResubmissionLog />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders resubmission events with their success status", async () => {
    renderWithQueryClient(<ResubmissionLog />);

    expect(await screen.findAllByText("Success")).toHaveLength(1);
    expect(screen.getAllByText("Failed")).toHaveLength(1);
  });

  it("shows error message on API failure", async () => {
    server.use(
      http.get("*/api/resubmissions", () => HttpResponse.json(null, { status: 500 })),
    );
    renderWithQueryClient(<ResubmissionLog />);
    expect(await screen.findByText("Failed to load resubmission log")).toBeInTheDocument();
  });

  it("shows pagination controls when total exceeds page size", async () => {
    const items = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      submitted_at: `2026-06-${String(12 + Math.floor(i / 10)).padStart(2, "0")}T${String(i % 24).padStart(2, "0")}:00:00Z`,
      success: i % 2 === 0,
      discord_notified: false,
    }));

    server.use(
      http.get("*/api/resubmissions", ({ request }) => {
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

    renderWithQueryClient(<ResubmissionLog />);

    expect(await screen.findByText(/page 1 of 2/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /previous/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /next/i })).not.toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    expect(await screen.findByText(/page 2 of 2/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /next/i })).toBeDisabled();
  });

  it("does not show pagination when all items fit on one page", async () => {
    renderWithQueryClient(<ResubmissionLog />);

    await screen.findByText("Success");
    expect(screen.queryByText(/page/i)).not.toBeInTheDocument();
  });
});
