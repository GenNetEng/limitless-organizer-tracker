import { fireEvent, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { adminConfig } from "../test/handlers";
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

  it("shows edit buttons for each config row", async () => {
    renderWithQueryClient(<AdminConfig />);

    await screen.findByText("4");

    const editButtons = screen.getAllByRole("button", { name: /edit/i });
    expect(editButtons.length).toBeGreaterThanOrEqual(7);
  });

  it("clicking edit reveals an input field with the current value", async () => {
    renderWithQueryClient(<AdminConfig />);

    await screen.findByText("200");

    const editButtons = screen.getAllByRole("button", { name: /edit/i });
    fireEvent.click(editButtons[3]);

    const input = screen.getByRole("textbox");
    expect(input).toHaveValue("200");
  });

  it("clicking cancel reverts to display mode without saving", async () => {
    renderWithQueryClient(<AdminConfig />);

    await screen.findByText("200");

    const editButtons = screen.getAllByRole("button", { name: /edit/i });
    fireEvent.click(editButtons[3]);

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "999" } });

    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
  });

  it("clicking save sends PUT and shows updated value", async () => {
    server.use(
      http.put("*/api/admin/config", async ({ request }) => {
        const body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ ...adminConfig, ...body });
      }),
    );

    renderWithQueryClient(<AdminConfig />);

    await screen.findByText("200");

    const editButtons = screen.getAllByRole("button", { name: /edit/i });
    fireEvent.click(editButtons[3]);

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "42" } });

    fireEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    });
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("shows error feedback when save fails", async () => {
    server.use(
      http.put("*/api/admin/config", () =>
        HttpResponse.json({ detail: "bad" }, { status: 422 }),
      ),
    );

    renderWithQueryClient(<AdminConfig />);

    await screen.findByText("200");

    const editButtons = screen.getAllByRole("button", { name: /edit/i });
    fireEvent.click(editButtons[3]);

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "bad" } });

    fireEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(screen.getByText(/failed/i)).toBeInTheDocument();
    });
  });
});
