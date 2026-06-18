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

/** Non-frontier organizers — the general population scatter series. */
export function toScatterData(estimate: WaitEstimate): ScatterPoint[] {
  return estimate.points
    .filter((p) => !p.is_frontier)
    .map((p) => ({
      organizerId: p.organizer_id,
      timestamp: Date.parse(`${p.first_tournament_date}T00:00:00Z`),
    }));
}

/** Frontier organizers — the fastest-observed onboarding lower-envelope series. */
export function toFrontierScatterData(estimate: WaitEstimate): ScatterPoint[] {
  return estimate.points
    .filter((p) => p.is_frontier)
    .map((p) => ({
      organizerId: p.organizer_id,
      timestamp: Date.parse(`${p.first_tournament_date}T00:00:00Z`),
    }));
}

export function toFittedLineData(estimate: WaitEstimate): ScatterPoint[] {
  const pointIds = estimate.points.map((p) => p.organizer_id);
  const targetIds = estimate.organizer_id !== null ? [estimate.organizer_id] : [];
  const allIds = [...pointIds, ...targetIds];
  const minId = Math.min(...allIds);
  const maxId = Math.max(...allIds);

  const ordinalToTimestamp = (ordinal: number) => {
    const clamped = Math.max(MIN_ORDINAL, Math.min(MAX_ORDINAL, ordinal));
    return (clamped - EPOCH_ORDINAL) * MS_PER_DAY;
  };

  return [minId, maxId].map((organizerId) => ({
    organizerId,
    timestamp: ordinalToTimestamp(estimate.slope * organizerId + estimate.intercept),
  }));
}
