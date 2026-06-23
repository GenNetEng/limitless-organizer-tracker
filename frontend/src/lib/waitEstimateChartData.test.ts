import { describe, expect, it } from "vitest";
import type { WaitEstimate } from "../api/client";
import { toFittedLineData, toFrontierScatterData, toScatterData } from "./waitEstimateChartData";

const estimate: WaitEstimate = {
  organizer_id: 400,
  slope: 1,
  r_squared: 0.9,
  projected_active_date: "2026-04-01",
  sample_size: 3,
  frontier_size: 2,
  total_points: 3,
  fitted_line: [
    { organizer_id: 100, projected_date: "2026-01-01" },
    { organizer_id: 400, projected_date: "2026-04-01" },
  ],
  points: [
    { organizer_id: 100, first_tournament_date: "2026-01-01", is_frontier: true },
    { organizer_id: 200, first_tournament_date: "2026-02-01", is_frontier: false },
    { organizer_id: 300, first_tournament_date: "2026-03-03", is_frontier: true },
  ],
};

const estimateNoTarget: WaitEstimate = {
  ...estimate,
  organizer_id: null,
  projected_active_date: null,
  fitted_line: [
    { organizer_id: 100, projected_date: "2026-01-01" },
    { organizer_id: 300, projected_date: "2026-03-03" },
  ],
};

describe("toScatterData", () => {
  it("maps non-frontier points to {organizerId, timestamp}", () => {
    expect(toScatterData(estimate)).toEqual([
      { organizerId: 200, timestamp: Date.parse("2026-02-01T00:00:00Z") },
    ]);
  });

  it("returns an empty array when all points are on the frontier", () => {
    const allFrontier: WaitEstimate = {
      ...estimate,
      points: estimate.points.map((p) => ({ ...p, is_frontier: true })),
    };
    expect(toScatterData(allFrontier)).toEqual([]);
  });
});

describe("toFrontierScatterData", () => {
  it("maps frontier points to {organizerId, timestamp}", () => {
    expect(toFrontierScatterData(estimate)).toEqual([
      { organizerId: 100, timestamp: Date.parse("2026-01-01T00:00:00Z") },
      { organizerId: 300, timestamp: Date.parse("2026-03-03T00:00:00Z") },
    ]);
  });

  it("returns an empty array when no points are on the frontier", () => {
    const noFrontier: WaitEstimate = {
      ...estimate,
      points: estimate.points.map((p) => ({ ...p, is_frontier: false })),
    };
    expect(toFrontierScatterData(noFrontier)).toEqual([]);
  });
});

describe("toFittedLineData", () => {
  it("returns two endpoints from the backend-computed fitted_line", () => {
    expect(toFittedLineData(estimate)).toEqual([
      { organizerId: 100, timestamp: Date.parse("2026-01-01T00:00:00Z") },
      { organizerId: 400, timestamp: Date.parse("2026-04-01T00:00:00Z") },
    ]);
  });

  it("uses the fitted_line range when organizer_id is null", () => {
    expect(toFittedLineData(estimateNoTarget)).toEqual([
      { organizerId: 100, timestamp: Date.parse("2026-01-01T00:00:00Z") },
      { organizerId: 300, timestamp: Date.parse("2026-03-03T00:00:00Z") },
    ]);
  });
});
