import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { EventLogViewer } from "./EventLogViewer";

describe("EventLogViewer", () => {
  it("renders event log entries from the API", async () => {
    renderWithQueryClient(<EventLogViewer />);

    expect(await screen.findByText("ingest_tournaments completed")).toBeInTheDocument();
    expect(screen.getByText("ingest_tournaments started")).toBeInTheDocument();
    expect(screen.getByText("Resubmit button not found")).toBeInTheDocument();
  });

  it("displays severity badges for each entry", async () => {
    renderWithQueryClient(<EventLogViewer />);

    await screen.findByText("ingest_tournaments completed");

    const infoBadges = screen.getAllByText("info");
    expect(infoBadges.length).toBe(2);
    expect(screen.getByText("error")).toBeInTheDocument();
  });

  it("displays event type and source for each entry", async () => {
    renderWithQueryClient(<EventLogViewer />);

    await screen.findByText("ingest_tournaments completed");

    expect(screen.getAllByText("celery").length).toBe(2);
    expect(screen.getByText("resubmit")).toBeInTheDocument();
    expect(screen.getByText("task.completed")).toBeInTheDocument();
    expect(screen.getByText("scraper.error")).toBeInTheDocument();
  });

  it("shows a loading state while fetching", () => {
    renderWithQueryClient(<EventLogViewer />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
