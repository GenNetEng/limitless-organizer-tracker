import { describe, expect, it } from "vitest";
import { toActivityChartData, mergeOnboardingOverlay } from "./activityChartData";

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

describe("mergeOnboardingOverlay", () => {
  it("merges onboarding counts into existing activity chart data", () => {
    const activity = [
      { period: "2026-06-01", label: "Jun 1", count: 5 },
      { period: "2026-06-08", label: "Jun 8", count: 3 },
    ];
    const onboarding = [
      { period: "2026-06-01", count: 2 },
      { period: "2026-06-08", count: 1 },
    ];

    const result = mergeOnboardingOverlay(activity, onboarding);

    expect(result).toEqual([
      { period: "2026-06-01", label: "Jun 1", count: 5, onboarded: 2 },
      { period: "2026-06-08", label: "Jun 8", count: 3, onboarded: 1 },
    ]);
  });

  it("adds onboarding-only periods with zero activity count", () => {
    const activity = [
      { period: "2026-06-01", label: "Jun 1", count: 5 },
    ];
    const onboarding = [
      { period: "2026-06-01", count: 2 },
      { period: "2026-06-15", count: 3 },
    ];

    const result = mergeOnboardingOverlay(activity, onboarding);

    expect(result).toEqual([
      { period: "2026-06-01", label: "Jun 1", count: 5, onboarded: 2 },
      { period: "2026-06-15", label: "Jun 15", count: 0, onboarded: 3 },
    ]);
  });

  it("preserves activity periods that have no onboarding data", () => {
    const activity = [
      { period: "2026-06-01", label: "Jun 1", count: 5 },
      { period: "2026-06-08", label: "Jun 8", count: 3 },
    ];
    const onboarding = [
      { period: "2026-06-01", count: 2 },
    ];

    const result = mergeOnboardingOverlay(activity, onboarding);

    expect(result).toEqual([
      { period: "2026-06-01", label: "Jun 1", count: 5, onboarded: 2 },
      { period: "2026-06-08", label: "Jun 8", count: 3, onboarded: 0 },
    ]);
  });

  it("returns empty array when both inputs are empty", () => {
    expect(mergeOnboardingOverlay([], [])).toEqual([]);
  });

  it("sorts merged data by period", () => {
    const activity = [
      { period: "2026-06-08", label: "Jun 8", count: 3 },
    ];
    const onboarding = [
      { period: "2026-06-01", count: 2 },
    ];

    const result = mergeOnboardingOverlay(activity, onboarding);

    expect(result[0].period).toBe("2026-06-01");
    expect(result[1].period).toBe("2026-06-08");
  });
});
