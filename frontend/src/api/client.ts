const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
const API_KEY = import.meta.env.VITE_API_KEY ?? "";

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
  review_note: string | null;
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
  is_frontier: boolean;
}

export interface WaitEstimate {
  organizer_id: number | null;
  slope: number;
  intercept: number;
  r_squared: number;
  projected_active_date: string | null;
  sample_size: number;
  frontier_size: number;
  points: WaitEstimatePoint[];
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function getJson<T>(path: string): Promise<T> {
  const headers: Record<string, string> = {};
  if (API_KEY) {
    headers["X-API-Key"] = API_KEY;
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { headers });
  if (!response.ok) {
    throw new ApiError(`Request to ${path} failed with status ${response.status}`, response.status);
  }
  return (await response.json()) as T;
}

export function getStatusHistory(limit = 50, offset = 0): Promise<Page<StatusCheck>> {
  return getJson<Page<StatusCheck>>(`/api/status-history?limit=${limit}&offset=${offset}`);
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

export function getWaitEstimate(organizerId?: number): Promise<WaitEstimate> {
  const query =
    organizerId !== undefined ? `?organizer_id=${encodeURIComponent(organizerId)}` : "";
  return getJson<WaitEstimate>(`/api/organizers/wait-estimate${query}`);
}

export interface TournamentEntry {
  tournament_id: string;
  name: string;
  date: string;
  game: string;
  players: number;
}

export interface OrganizerProfile {
  organizer_id: number;
  name: string;
  upcoming_tournaments: TournamentEntry[];
  recent_tournaments: TournamentEntry[];
  onboarded_at: string | null;
  first_tournament_date: string | null;
}

export interface HighestOrganizerId {
  organizer_id: number;
}

export function scrapeOrganizerProfile(organizerId: number): Promise<OrganizerProfile> {
  return getJson<OrganizerProfile>(`/api/organizers/${encodeURIComponent(organizerId)}/scrape`);
}

export function getHighestOrganizerId(): Promise<HighestOrganizerId> {
  return getJson<HighestOrganizerId>("/api/organizers/highest-id");
}
