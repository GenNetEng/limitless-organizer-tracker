import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
import { ApplicationStatCards } from "./ApplicationStatCards";

describe("ApplicationStatCards", () => {
  it("shows loading state initially", () => {
    renderWithQueryClient(<ApplicationStatCards />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders current status badge", async () => {
    renderWithQueryClient(<ApplicationStatCards />);
    expect(await screen.findByText(/rejected/i)).toBeInTheDocument();
  });

  it("renders last check time", async () => {
    renderWithQueryClient(<ApplicationStatCards />);
    await screen.findByText(/rejected/i);
    expect(screen.getByText(/last check/i)).toBeInTheDocument();
  });

  it("renders total resubmissions count", async () => {
    renderWithQueryClient(<ApplicationStatCards />);
    expect(await screen.findByText("2")).toBeInTheDocument();
    expect(screen.getByText(/total resubmissions/i)).toBeInTheDocument();
  });

  it("renders last resubmission time", async () => {
    renderWithQueryClient(<ApplicationStatCards />);
    await screen.findByText("2");
    expect(screen.getByText(/last resubmission/i)).toBeInTheDocument();
  });

  it("shows no data message when status history is empty", async () => {
    server.use(
      http.get("*/api/status-history", () =>
        HttpResponse.json({ items: [], total: 0, limit: 1, offset: 0 }),
      ),
    );
    renderWithQueryClient(<ApplicationStatCards />);
    expect(await screen.findByText(/no status checks/i)).toBeInTheDocument();
  });

  it("shows no resubmissions message when none exist", async () => {
    server.use(
      http.get("*/api/resubmissions", () =>
        HttpResponse.json({ items: [], total: 0, limit: 1, offset: 0 }),
      ),
    );
    renderWithQueryClient(<ApplicationStatCards />);
    expect(await screen.findByText(/no resubmissions/i)).toBeInTheDocument();
  });

  it("shows error state on API failure", async () => {
    server.use(
      http.get("*/api/status-history", () =>
        HttpResponse.json({ detail: "server error" }, { status: 500 }),
      ),
    );
    renderWithQueryClient(<ApplicationStatCards />);
    expect(await screen.findByText(/failed to load/i)).toBeInTheDocument();
  });
});
