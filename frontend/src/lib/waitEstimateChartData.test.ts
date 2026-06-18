import { describe, expect, it } from "vitest";
import type { WaitEstimate } from "../api/client";
import { toFittedLineData, toFrontierScatterData, toScatterData } from "./waitEstimateChartData";

const MS_PER_DAY = 86_400_000;

// Python date.min/date.max ordinals converted to Unix-epoch ms timestamps,
// matching the clamp backend's get_wait_estimate applies to projected_active_date.
const MIN_TIMESTAMP = -62_135_596_800_000;
const MAX_TIMESTAMP = 253_402_214_400_000;

// slope=1, intercept=719163 (= date(1970, 1, 1).toordinal()) makes the
// fitted line's ordinal-to-timestamp conversion line up with organizer_id
// directly: ordinal = organizer_id + 719163 -> timestamp = organizer_id days.
const estimate: WaitEstimate = {
  organizer_id: 400,
  slope: 1,
  intercept: 719163,
  r_squared: 0.9,
  projected_active_date: "2026-04-01",
  sample_size: 3,
  frontier_size: 2,
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
  it("returns two endpoints spanning min/max organizer_id across points and the target", () => {
    expect(toFittedLineData(estimate)).toEqual([
      { organizerId: 100, timestamp: 100 * MS_PER_DAY },
      { organizerId: 400, timestamp: 400 * MS_PER_DAY },
    ]);
  });

  it("uses only points range when organizer_id is null", () => {
    expect(toFittedLineData(estimateNoTarget)).toEqual([
      { organizerId: 100, timestamp: 100 * MS_PER_DAY },
      { organizerId: 300, timestamp: 300 * MS_PER_DAY },
    ]);
  });

  it("clamps the upper endpoint to date.max when the projected ordinal overflows", () => {
    const extreme: WaitEstimate = { ...estimate, organizer_id: 1_000_000_000_000 };

    const [, maxPoint] = toFittedLineData(extreme);

    expect(maxPoint).toEqual({ organizerId: 1_000_000_000_000, timestamp: MAX_TIMESTAMP });
  });

  it("clamps the lower endpoint to date.min when the projected ordinal underflows", () => {
    const extreme: WaitEstimate = { ...estimate, organizer_id: -1_000_000_000_000 };

    const [minPoint] = toFittedLineData(extreme);

    expect(minPoint).toEqual({ organizerId: -1_000_000_000_000, timestamp: MIN_TIMESTAMP });
  });
});
