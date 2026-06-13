import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
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
});
