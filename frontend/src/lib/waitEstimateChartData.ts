import type { WaitEstimate } from "../api/client";

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

/** Two endpoints of the backend-computed fitted regression line. */
export function toFittedLineData(estimate: WaitEstimate): ScatterPoint[] {
  return estimate.fitted_line.map((ep) => ({
    organizerId: ep.organizer_id,
    timestamp: Date.parse(`${ep.projected_date}T00:00:00Z`),
  }));
}
