import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { Dashboard } from "./Dashboard";

describe("Dashboard", () => {
  it("renders the status history and resubmission log sections", async () => {
    renderWithQueryClient(<Dashboard />);

    expect(screen.getByRole("heading", { name: /status history/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /resubmission log/i })).toBeInTheDocument();

    expect(await screen.findByText("Pending")).toBeInTheDocument();
    expect(await screen.findAllByText("Success")).toHaveLength(1);
  });

  it("renders the organizer activity and wait time estimator sections", async () => {
    renderWithQueryClient(<Dashboard />);

    expect(screen.getByRole("heading", { name: /organizer activity/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /wait time estimator/i })).toBeInTheDocument();

    expect(await screen.findByText("Jun 1: 2")).toBeInTheDocument();
  });
});
