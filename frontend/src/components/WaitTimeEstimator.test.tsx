import { fireEvent, screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
import { WaitTimeEstimator } from "./WaitTimeEstimator";

describe("WaitTimeEstimator", () => {
  it("renders an organizer ID input and a submit button on load", () => {
    renderWithQueryClient(<WaitTimeEstimator />);

    expect(screen.getByLabelText(/organizer id/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /estimate/i })).toBeInTheDocument();
  });

  it("does not render a game selector", () => {
    renderWithQueryClient(<WaitTimeEstimator />);

    expect(screen.queryByLabelText(/game/i)).not.toBeInTheDocument();
  });

  it("renders the scatter chart on load without requiring organizer ID input", async () => {
    renderWithQueryClient(<WaitTimeEstimator />);

    // slope and R² are rendered without user submitting a form
    expect(await screen.findByText(/0\.5000/)).toBeInTheDocument();
    expect(screen.getByText(/0\.950/)).toBeInTheDocument();
    expect(screen.getByText(/frontier/i)).toBeInTheDocument();
  });

  it("does not show projected active date until an organizer ID is submitted", async () => {
    renderWithQueryClient(<WaitTimeEstimator />);

    // Wait for initial chart to render
    await screen.findByText(/0\.5000/);
    expect(screen.queryByText(/projected active date/i)).not.toBeInTheDocument();
  });

  it("shows projected active date after submitting an organizer ID", async () => {
    renderWithQueryClient(<WaitTimeEstimator />);

    await screen.findByText(/0\.5000/);

    fireEvent.change(screen.getByLabelText(/organizer id/i), { target: { value: "400" } });
    fireEvent.click(screen.getByRole("button", { name: /estimate/i }));

    expect(await screen.findByText(/projected active date/i)).toBeInTheDocument();
    expect(screen.getByText("2026-04-01")).toBeInTheDocument();
  });

  it("shows the frontier size stat on load", async () => {
    renderWithQueryClient(<WaitTimeEstimator />);

    expect(await screen.findByText(/frontier organizers/i)).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("shows a message when there isn't enough data to estimate", async () => {
    server.use(
      http.get("*/api/organizers/wait-estimate", () =>
        HttpResponse.json({ detail: "not enough activity data to estimate" }, { status: 404 }),
      ),
    );

    renderWithQueryClient(<WaitTimeEstimator />);

    expect(await screen.findByText(/not enough data/i)).toBeInTheDocument();
  });

  it("shows a generic failure message for a non-404 error", async () => {
    server.use(
      http.get("*/api/organizers/wait-estimate", () =>
        HttpResponse.json({ detail: "internal error" }, { status: 500 }),
      ),
    );

    renderWithQueryClient(<WaitTimeEstimator />);

    expect(await screen.findByText(/failed to load/i)).toBeInTheDocument();
    expect(screen.queryByText(/not enough data/i)).not.toBeInTheDocument();
  });
});
