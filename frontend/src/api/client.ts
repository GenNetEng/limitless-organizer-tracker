const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export type ApplicationStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "expired"
  | "unknown";

export interface StatusCheck {
  id: number;
  checked_at: string;
  status: ApplicationStatus;
  raw_text: string | null;
}

export interface ResubmissionEvent {
  id: number;
  submitted_at: string;
  success: boolean;
  discord_notified: boolean;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ActivityBucket {
  period: string;
  count: number;
}

export interface WaitEstimatePoint {
  organizer_id: number;
  first_tournament_date: string;
}

export interface WaitEstimate {
  organizer_id: number;
  game: string;
  slope: number;
  intercept: number;
  r_squared: number;
  projected_active_date: string;
  sample_size: number;
  points: WaitEstimatePoint[];
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request to ${path} failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export function getStatusHistory(): Promise<Page<StatusCheck>> {
  return getJson<Page<StatusCheck>>("/api/status-history");
}

export function getResubmissions(): Promise<Page<ResubmissionEvent>> {
  return getJson<Page<ResubmissionEvent>>("/api/resubmissions");
}

export function getGames(): Promise<string[]> {
  return getJson<string[]>("/api/games");
}

export function getOrganizerActivity(game: string | null): Promise<ActivityBucket[]> {
  const query = game ? `?game=${encodeURIComponent(game)}` : "";
  return getJson<ActivityBucket[]>(`/api/organizers/activity${query}`);
}

export function getWaitEstimate(organizerId: number, game: string): Promise<WaitEstimate> {
  const params = new URLSearchParams({ organizer_id: String(organizerId), game });
  return getJson<WaitEstimate>(`/api/organizers/wait-estimate?${params.toString()}`);
}
