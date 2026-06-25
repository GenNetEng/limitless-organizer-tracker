import { screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithQueryClient } from "../test/renderWithQueryClient";
import { OnboardingDelta } from "./OnboardingDelta";

describe("OnboardingDelta", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-06-25T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows a loading state", () => {
    renderWithQueryClient(<OnboardingDelta />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("displays average and median delta days", async () => {
    renderWithQueryClient(<OnboardingDelta />);

    expect(await screen.findByText(/13\.3/)).toBeInTheDocument();
    expect(screen.getByText(/10/)).toBeInTheDocument();
  });

  it("displays the sample count and organizers label", async () => {
    renderWithQueryClient(<OnboardingDelta />);

    await screen.findByText("13.3");
    expect(screen.getByText("organizers")).toBeInTheDocument();
  });

  it("shows the ID threshold note", async () => {
    renderWithQueryClient(<OnboardingDelta />);

    await screen.findByText(/13\.3/);
    expect(screen.getByText(/2723/)).toBeInTheDocument();
  });
});
