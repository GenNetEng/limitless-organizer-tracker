import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { server } from "../test/server";
import { ResubmissionLog } from "./ResubmissionLog";

describe("ResubmissionLog", () => {
  it("shows a loading state before the resubmission log loads", () => {
    renderWithQueryClient(<ResubmissionLog />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders resubmission events with their success status", async () => {
    renderWithQueryClient(<ResubmissionLog />);

    expect(await screen.findAllByText("Success")).toHaveLength(1);
    expect(screen.getAllByText("Failed")).toHaveLength(1);
  });

  it("shows error message on API failure", async () => {
    server.use(
      http.get("*/api/resubmissions", () => HttpResponse.json(null, { status: 500 })),
    );
    renderWithQueryClient(<ResubmissionLog />);
    expect(await screen.findByText("Failed to load resubmission log.")).toBeInTheDocument();
  });
});
