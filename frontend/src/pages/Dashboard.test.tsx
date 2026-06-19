import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { Dashboard } from "./Dashboard";

describe("Dashboard", () => {
  it("renders the tab navigation with three tabs", () => {
    renderWithQueryClient(<Dashboard />);

    expect(screen.getByRole("tab", { name: /my application/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /organizer growth/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /organizer lookup/i })).toBeInTheDocument();
  });

  it("shows the application tab by default with status history and resubmission log", async () => {
    renderWithQueryClient(<Dashboard />);

    expect(screen.getByRole("heading", { name: /status history/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /resubmission log/i })).toBeInTheDocument();

    expect(await screen.findByText("Pending")).toBeInTheDocument();
    expect(await screen.findAllByText("Success")).toHaveLength(1);
  });

  it("switches to organizer growth tab and shows activity chart and wait estimator", async () => {
    renderWithQueryClient(<Dashboard />);

    fireEvent.click(screen.getByRole("tab", { name: /organizer growth/i }));

    expect(screen.getByRole("heading", { name: /organizer activity/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /wait time estimator/i })).toBeInTheDocument();

    expect(await screen.findByText("Jun 1: 2")).toBeInTheDocument();
  });

  it("switches to organizer lookup tab and shows highest ID and profile sections", async () => {
    renderWithQueryClient(<Dashboard />);

    fireEvent.click(screen.getByRole("tab", { name: /organizer lookup/i }));

    expect(screen.getByRole("heading", { name: /highest organizer id/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /organizer profile/i })).toBeInTheDocument();

    expect(await screen.findByText("2720")).toBeInTheDocument();
  });

  it("hides other tabs' content when switching", async () => {
    renderWithQueryClient(<Dashboard />);

    await screen.findByText("Pending");

    fireEvent.click(screen.getByRole("tab", { name: /organizer growth/i }));

    expect(screen.queryByRole("heading", { name: /status history/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /resubmission log/i })).not.toBeInTheDocument();
  });
});
