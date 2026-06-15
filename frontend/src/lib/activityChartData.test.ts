import { describe, expect, it } from "vitest";
import { toActivityChartData } from "./activityChartData";

describe("toActivityChartData", () => {
  it("maps buckets to chart data with a formatted label", () => {
    const result = toActivityChartData([
      { period: "2026-06-01", count: 2 },
      { period: "2026-06-08", count: 1 },
    ]);

    expect(result).toEqual([
      { period: "2026-06-01", label: "Jun 1", count: 2 },
      { period: "2026-06-08", label: "Jun 8", count: 1 },
    ]);
  });

  it("returns an empty array for no buckets", () => {
    expect(toActivityChartData([])).toEqual([]);
  });
});
