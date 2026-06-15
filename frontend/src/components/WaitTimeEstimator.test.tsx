import { fireEvent, screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
import { WaitTimeEstimator } from "./WaitTimeEstimator";

async function fillAndSubmit() {
  fireEvent.change(screen.getByLabelText(/organizer id/i), { target: { value: "400" } });
  await screen.findByRole("option", { name: "PTCG" });
  fireEvent.change(screen.getByLabelText(/game/i), { target: { value: "PTCG" } });
  fireEvent.click(screen.getByRole("button", { name: /estimate/i }));
}

describe("WaitTimeEstimator", () => {
  it("renders an organizer ID input, a game select, and a submit button", async () => {
    renderWithQueryClient(<WaitTimeEstimator />);

    expect(screen.getByLabelText(/organizer id/i)).toBeInTheDocument();
    expect(await screen.findByRole("option", { name: "PTCG" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "POCKET" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /estimate/i })).toBeInTheDocument();
  });

  it("does not fetch an estimate before the form is submitted", () => {
    renderWithQueryClient(<WaitTimeEstimator />);

    expect(screen.queryByText(/calculating wait estimate/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/projected active date/i)).not.toBeInTheDocument();
  });

  it("submits the form and renders the regression result", async () => {
    renderWithQueryClient(<WaitTimeEstimator />);

    await fillAndSubmit();

    expect(await screen.findByText("2026-04-01")).toBeInTheDocument();
    expect(screen.getByText("0.5000")).toBeInTheDocument();
    expect(screen.getByText("0.950")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("shows a message when there isn't enough data to estimate", async () => {
    server.use(
      http.get("*/api/organizers/wait-estimate", () =>
        HttpResponse.json({ detail: "not enough activity data to estimate" }, { status: 404 }),
      ),
    );

    renderWithQueryClient(<WaitTimeEstimator />);

    await fillAndSubmit();

    expect(await screen.findByText(/not enough data/i)).toBeInTheDocument();
  });
});
