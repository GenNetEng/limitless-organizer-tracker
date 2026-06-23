import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
import { AdminConfig } from "./AdminConfig";

describe("AdminConfig", () => {
  it("renders configuration values from the API", async () => {
    renderWithQueryClient(<AdminConfig />);

    expect(await screen.findByText("4")).toBeInTheDocument();
    expect(screen.getByText("09:00,21:00")).toBeInTheDocument();
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("24")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("displays configuration labels", async () => {
    renderWithQueryClient(<AdminConfig />);

    await screen.findByText("4");

    expect(screen.getByText(/status check interval/i)).toBeInTheDocument();
    expect(screen.getByText(/resubmit times/i)).toBeInTheDocument();
    expect(screen.getByText(/tournament ingest interval/i)).toBeInTheDocument();
    expect(screen.getByText(/tournament ingest limit/i)).toBeInTheDocument();
    expect(screen.getByText(/backfill months/i)).toBeInTheDocument();
    expect(screen.getByText(/organizer scan interval/i)).toBeInTheDocument();
    expect(screen.getByText(/organizer scan limit/i)).toBeInTheDocument();
  });

  it("shows a loading state while fetching", () => {
    renderWithQueryClient(<AdminConfig />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows error message on API failure", async () => {
    server.use(
      http.get("*/api/admin/config", () => HttpResponse.json(null, { status: 500 })),
    );
    renderWithQueryClient(<AdminConfig />);
    expect(await screen.findByText("Failed to load configuration")).toBeInTheDocument();
  });
});
