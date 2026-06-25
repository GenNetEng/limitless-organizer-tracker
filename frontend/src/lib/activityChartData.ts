import type { ActivityBucket } from "../api/client";
import { formatDateShort } from "./formatDate";

export interface ActivityChartDatum {
  period: string;
  label: string;
  count: number;
  onboarded?: number;
}

export function toActivityChartData(buckets: ActivityBucket[]): ActivityChartDatum[] {
  return buckets.map((bucket) => ({
    period: bucket.period,
    label: formatDateShort(bucket.period),
    count: bucket.count,
  }));
}

export function mergeOnboardingOverlay(
  activity: ActivityChartDatum[],
  onboarding: ActivityBucket[],
): ActivityChartDatum[] {
  const onboardingMap = new Map(onboarding.map((b) => [b.period, b.count]));
  const activityMap = new Map(activity.map((d) => [d.period, d]));

  const allPeriods = new Set([...activityMap.keys(), ...onboardingMap.keys()]);
  const merged: ActivityChartDatum[] = [];

  for (const period of allPeriods) {
    const existing = activityMap.get(period);
    merged.push({
      period,
      label: existing?.label ?? formatDateShort(period),
      count: existing?.count ?? 0,
      onboarded: onboardingMap.get(period) ?? 0,
    });
  }

  return merged.sort((a, b) => a.period.localeCompare(b.period));
}
