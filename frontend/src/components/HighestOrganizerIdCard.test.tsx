import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
import { HighestOrganizerIdCard } from "./HighestOrganizerIdCard";

describe("HighestOrganizerIdCard", () => {
  it("shows a loading state initially", () => {
    renderWithQueryClient(<HighestOrganizerIdCard />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders the highest organizer ID from the API", async () => {
    renderWithQueryClient(<HighestOrganizerIdCard />);

    expect(await screen.findByText("2720")).toBeInTheDocument();
    expect(screen.getByText(/highest organizer id/i)).toBeInTheDocument();
  });

  it("shows an error message when the API returns 404", async () => {
    server.use(
      http.get("*/api/organizers/highest-id", () =>
        HttpResponse.json({ detail: "no organizer data available" }, { status: 404 }),
      ),
    );

    renderWithQueryClient(<HighestOrganizerIdCard />);

    expect(await screen.findByText(/no organizer data/i)).toBeInTheDocument();
  });
});
