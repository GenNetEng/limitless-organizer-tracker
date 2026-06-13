import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { Dashboard } from "./Dashboard";

describe("Dashboard", () => {
  it("renders the status history and resubmission log sections", async () => {
    renderWithQueryClient(<Dashboard />);

    expect(screen.getByRole("heading", { name: /status history/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /resubmission log/i })).toBeInTheDocument();

    expect(await screen.findByText("check 2")).toBeInTheDocument();
    expect(await screen.findAllByText("Success")).toHaveLength(1);
  });
});
