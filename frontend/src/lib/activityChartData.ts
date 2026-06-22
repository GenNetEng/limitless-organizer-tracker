import type { ActivityBucket } from "../api/client";
import { formatDateShort } from "./formatDate";

export interface ActivityChartDatum {
  period: string;
  label: string;
  count: number;
}

export function toActivityChartData(buckets: ActivityBucket[]): ActivityChartDatum[] {
  return buckets.map((bucket) => ({
    period: bucket.period,
    label: formatDateShort(bucket.period),
    count: bucket.count,
  }));
}
