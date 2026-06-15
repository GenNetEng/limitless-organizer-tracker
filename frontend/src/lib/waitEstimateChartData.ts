import type { WaitEstimate } from "../api/client";

// Python's date(1970, 1, 1).toordinal() — converts the regression's
// ordinal-day units (from app/analytics/regression.py) to Unix epoch days.
const EPOCH_ORDINAL = 719163;
const MS_PER_DAY = 86_400_000;

// date.min.toordinal() / date.max.toordinal() — mirrors the clamp
// backend's get_wait_estimate applies to projected_active_date, so the
// fitted line never asks Date for a value outside Python's date range.
const MIN_ORDINAL = 1;
const MAX_ORDINAL = 3_652_059;

export interface ScatterPoint {
  organizerId: number;
  timestamp: number;
}

export function toScatterData(estimate: WaitEstimate): ScatterPoint[] {
  return estimate.points.map((point) => ({
    organizerId: point.organizer_id,
    timestamp: Date.parse(`${point.first_tournament_date}T00:00:00Z`),
  }));
}

export function toFittedLineData(estimate: WaitEstimate): ScatterPoint[] {
  const organizerIds = [estimate.organizer_id, ...estimate.points.map((point) => point.organizer_id)];
  const minId = Math.min(...organizerIds);
  const maxId = Math.max(...organizerIds);

  const ordinalToTimestamp = (ordinal: number) => {
    const clamped = Math.max(MIN_ORDINAL, Math.min(MAX_ORDINAL, ordinal));
    return (clamped - EPOCH_ORDINAL) * MS_PER_DAY;
  };

  return [minId, maxId].map((organizerId) => ({
    organizerId,
    timestamp: ordinalToTimestamp(estimate.slope * organizerId + estimate.intercept),
  }));
}
