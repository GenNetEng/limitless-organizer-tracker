import { fireEvent, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
import { OrganizerProfile } from "./OrganizerProfile";

describe("OrganizerProfile", () => {
  it("renders a form to look up an organizer by ID", () => {
    renderWithQueryClient(<OrganizerProfile />);

    expect(screen.getByLabelText(/organizer id/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /look up/i })).toBeInTheDocument();
  });

  it("does not fetch until the user submits an organizer ID", () => {
    renderWithQueryClient(<OrganizerProfile />);

    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/test organizer/i)).not.toBeInTheDocument();
  });

  it("displays the organizer name and tournaments after submitting an ID", async () => {
    renderWithQueryClient(<OrganizerProfile />);

    fireEvent.change(screen.getByLabelText(/organizer id/i), { target: { value: "42" } });
    fireEvent.click(screen.getByRole("button", { name: /look up/i }));

    expect(await screen.findByText("Test Organizer")).toBeInTheDocument();
    expect(screen.getByText("Upcoming Cup")).toBeInTheDocument();
    expect(screen.getByText("Recent League")).toBeInTheDocument();
    expect(screen.getByText("Spring Open")).toBeInTheDocument();
  });

  it("shows upcoming and recent tournament sections separately", async () => {
    renderWithQueryClient(<OrganizerProfile />);

    fireEvent.change(screen.getByLabelText(/organizer id/i), { target: { value: "42" } });
    fireEvent.click(screen.getByRole("button", { name: /look up/i }));

    expect(await screen.findByText(/upcoming tournaments/i)).toBeInTheDocument();
    expect(screen.getByText(/recent tournaments/i)).toBeInTheDocument();
  });

  it("shows tournament details including game and player count", async () => {
    renderWithQueryClient(<OrganizerProfile />);

    fireEvent.change(screen.getByLabelText(/organizer id/i), { target: { value: "42" } });
    fireEvent.click(screen.getByRole("button", { name: /look up/i }));

    await screen.findByText("Recent League");
    expect(screen.getByText(/PTCG/)).toBeInTheDocument();
    expect(screen.getByText(/16 players/i)).toBeInTheDocument();
  });

  it("shows an error when the organizer is not found (404)", async () => {
    renderWithQueryClient(<OrganizerProfile />);

    fireEvent.change(screen.getByLabelText(/organizer id/i), { target: { value: "9999" } });
    fireEvent.click(screen.getByRole("button", { name: /look up/i }));

    expect(await screen.findByText(/organizer not found/i)).toBeInTheDocument();
  });

  it("shows a generic failure message for a non-404 error", async () => {
    server.use(
      http.get("*/api/organizers/:organizerId/scrape", () =>
        HttpResponse.json({ detail: "failed to reach Limitless" }, { status: 502 }),
      ),
    );

    renderWithQueryClient(<OrganizerProfile />);

    fireEvent.change(screen.getByLabelText(/organizer id/i), { target: { value: "42" } });
    fireEvent.click(screen.getByRole("button", { name: /look up/i }));

    expect(await screen.findByText(/failed to load/i)).toBeInTheDocument();
    expect(screen.queryByText(/organizer not found/i)).not.toBeInTheDocument();
  });

  it("shows 'no upcoming tournaments' when the list is empty", async () => {
    server.use(
      http.get("*/api/organizers/:organizerId/scrape", () =>
        HttpResponse.json({
          organizer_id: 42,
          name: "Empty Organizer",
          upcoming_tournaments: [],
          recent_tournaments: [],
        }),
      ),
    );

    renderWithQueryClient(<OrganizerProfile />);

    fireEvent.change(screen.getByLabelText(/organizer id/i), { target: { value: "42" } });
    fireEvent.click(screen.getByRole("button", { name: /look up/i }));

    await screen.findByText("Empty Organizer");
    expect(screen.getByText(/no upcoming tournaments/i)).toBeInTheDocument();
    expect(screen.getByText(/no recent tournaments/i)).toBeInTheDocument();
  });
});
