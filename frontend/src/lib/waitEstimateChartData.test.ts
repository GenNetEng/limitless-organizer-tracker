import { describe, expect, it } from "vitest";
import type { WaitEstimate } from "../api/client";
import { toFittedLineData, toScatterData } from "./waitEstimateChartData";

const MS_PER_DAY = 86_400_000;

// slope=1, intercept=719163 (= date(1970, 1, 1).toordinal()) makes the
// fitted line's ordinal-to-timestamp conversion line up with organizer_id
// directly: ordinal = organizer_id + 719163 -> timestamp = organizer_id days.
const estimate: WaitEstimate = {
  organizer_id: 400,
  game: "PTCG",
  slope: 1,
  intercept: 719163,
  r_squared: 0.9,
  projected_active_date: "2026-04-01",
  sample_size: 3,
  points: [
    { organizer_id: 100, first_tournament_date: "2026-01-01" },
    { organizer_id: 200, first_tournament_date: "2026-02-01" },
    { organizer_id: 300, first_tournament_date: "2026-03-03" },
  ],
};

describe("toScatterData", () => {
  it("maps each point's organizer_id and date to a timestamp", () => {
    expect(toScatterData(estimate)).toEqual([
      { organizerId: 100, timestamp: Date.parse("2026-01-01T00:00:00Z") },
      { organizerId: 200, timestamp: Date.parse("2026-02-01T00:00:00Z") },
      { organizerId: 300, timestamp: Date.parse("2026-03-03T00:00:00Z") },
    ]);
  });
});

describe("toFittedLineData", () => {
  it("returns two endpoints spanning the min/max organizer_id across points and the target", () => {
    expect(toFittedLineData(estimate)).toEqual([
      { organizerId: 100, timestamp: 100 * MS_PER_DAY },
      { organizerId: 400, timestamp: 400 * MS_PER_DAY },
    ]);
  });
});
