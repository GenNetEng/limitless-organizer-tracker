import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { TaskTriggers } from "./TaskTriggers";

describe("TaskTriggers", () => {
  it("renders task trigger buttons from the API", async () => {
    renderWithQueryClient(<TaskTriggers />);

    expect(await screen.findByRole("button", { name: /ingest_tournaments/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /scan_organizers/i })).toBeInTheDocument();
  });

  it("displays task descriptions", async () => {
    renderWithQueryClient(<TaskTriggers />);

    expect(
      await screen.findByText("Ingest tournament data from the Limitless API across all games"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Scan for newly onboarded organizer profiles"),
    ).toBeInTheDocument();
  });

  it("triggers a task when the button is clicked", async () => {
    renderWithQueryClient(<TaskTriggers />);

    const button = await screen.findByRole("button", { name: /ingest_tournaments/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/triggered/i)).toBeInTheDocument();
    });
  });

  it("shows a loading state while fetching", () => {
    renderWithQueryClient(<TaskTriggers />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
