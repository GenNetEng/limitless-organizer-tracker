import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { Diagnostics } from "./Diagnostics";

describe("Diagnostics", () => {
  it("renders health status indicators", async () => {
    renderWithQueryClient(<Diagnostics />);

    expect(await screen.findByText("Database")).toBeInTheDocument();
    expect(screen.getByText("Redis")).toBeInTheDocument();
    expect(screen.getByText("Celery Beat")).toBeInTheDocument();
  });

  it("shows healthy status when services are up", async () => {
    renderWithQueryClient(<Diagnostics />);

    await screen.findByText("Database");

    const healthyBadges = screen.getAllByText("Healthy");
    expect(healthyBadges.length).toBeGreaterThanOrEqual(3);
  });

  it("displays active celery workers", async () => {
    renderWithQueryClient(<Diagnostics />);

    expect(await screen.findByText("celery@worker1")).toBeInTheDocument();
  });

  it("displays last success timestamps per task", async () => {
    renderWithQueryClient(<Diagnostics />);

    await screen.findByText("Database");

    expect(screen.getByText("ingest_tournaments")).toBeInTheDocument();
    expect(screen.getByText("scan_new_organizers")).toBeInTheDocument();
  });

  it("shows a loading state while fetching", () => {
    renderWithQueryClient(<Diagnostics />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
