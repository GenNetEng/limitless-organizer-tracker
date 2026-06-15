import type { ActivityBucket } from "../api/client";

export interface ActivityChartDatum {
  period: string;
  label: string;
  count: number;
}

export function toActivityChartData(buckets: ActivityBucket[]): ActivityChartDatum[] {
  return buckets.map((bucket) => ({
    period: bucket.period,
    label: formatPeriodLabel(bucket.period),
    count: bucket.count,
  }));
}

function formatPeriodLabel(period: string): string {
  const date = new Date(`${period}T00:00:00Z`);
  return date.toLocaleDateString(undefined, {
    timeZone: "UTC",
    month: "short",
    day: "numeric",
  });
}
