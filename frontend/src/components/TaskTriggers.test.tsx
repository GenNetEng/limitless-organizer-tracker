import { fireEvent, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
import { TaskTriggers } from "./TaskTriggers";

describe("TaskTriggers", () => {
  it("renders trigger buttons for each task", async () => {
    renderWithQueryClient(<TaskTriggers />);

    const buttons = await screen.findAllByRole("button", { name: /run/i });
    expect(buttons).toHaveLength(2);
  });

  it("displays task descriptions and component badges", async () => {
    renderWithQueryClient(<TaskTriggers />);

    expect(
      await screen.findByText("Fetch recent tournaments from Limitless API"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Scan for newly onboarded organizers"),
    ).toBeInTheDocument();
    expect(screen.getByText("Tournaments")).toBeInTheDocument();
    expect(screen.getByText("Organizers")).toBeInTheDocument();
  });

  it("renders a table with column headers", async () => {
    renderWithQueryClient(<TaskTriggers />);

    await screen.findByText("Fetch recent tournaments from Limitless API");
    expect(screen.getByText("Component")).toBeInTheDocument();
    expect(screen.getByText("Task")).toBeInTheDocument();
    expect(screen.getByText("Action")).toBeInTheDocument();
  });

  it("triggers a task when the button is clicked", async () => {
    renderWithQueryClient(<TaskTriggers />);

    const buttons = await screen.findAllByRole("button", { name: /run/i });
    fireEvent.click(buttons[0]);

    await waitFor(() => {
      expect(screen.getByText(/triggered/i)).toBeInTheDocument();
    });
  });

  it("shows a loading state while fetching", () => {
    renderWithQueryClient(<TaskTriggers />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("shows error message on API failure", async () => {
    server.use(
      http.get("*/api/admin/tasks", () => HttpResponse.json(null, { status: 500 })),
    );
    renderWithQueryClient(<TaskTriggers />);
    expect(await screen.findByText("Failed to load tasks")).toBeInTheDocument();
  });
});
