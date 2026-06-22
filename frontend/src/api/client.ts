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

// Admin API types (FR20-FR23)

export interface EventLogEntry {
  id: number;
  timestamp: string;
  event_type: string;
  severity: string;
  source: string;
  message: string;
  details: Record<string, unknown> | unknown[] | null;
  correlation_id: string | null;
}

export interface Diagnostics {
  db_ok: boolean;
  redis_ok: boolean;
  celery_workers: string[];
  beat_ok: boolean;
  last_success_per_task: Record<string, string | null>;
}

export interface AdminConfig {
  application_status_check_interval_hours: number;
  resubmit_times_utc: string;
  tournament_ingest_interval_hours: number;
  tournament_ingest_limit: number;
  tournament_backfill_months: number;
  organizer_scan_interval_hours: number;
  organizer_scan_limit: number;
}

export interface TaskTriggerInfo {
  name: string;
  endpoint: string;
  method: string;
  description: string;
}

async function postJson<T>(path: string): Promise<T> {
  const headers: Record<string, string> = {};
  if (API_KEY) {
    headers["X-API-Key"] = API_KEY;
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers,
  });
  if (!response.ok) {
    throw new ApiError(`Request to ${path} failed with status ${response.status}`, response.status);
  }
  return (await response.json()) as T;
}

export function getEventLog(
  params: { limit?: number; offset?: number; event_type?: string; severity?: string; source?: string } = {},
): Promise<Page<EventLogEntry>> {
  const search = new URLSearchParams();
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  if (params.event_type) search.set("event_type", params.event_type);
  if (params.severity) search.set("severity", params.severity);
  if (params.source) search.set("source", params.source);
  const qs = search.toString();
  return getJson<Page<EventLogEntry>>(`/api/admin/event-log${qs ? `?${qs}` : ""}`);
}

export function getDiagnostics(): Promise<Diagnostics> {
  return getJson<Diagnostics>("/api/admin/diagnostics");
}

export function getAdminConfig(): Promise<AdminConfig> {
  return getJson<AdminConfig>("/api/admin/config");
}

export function getTaskTriggers(): Promise<TaskTriggerInfo[]> {
  return getJson<TaskTriggerInfo[]>("/api/admin/tasks");
}

export function triggerTask(endpoint: string): Promise<unknown> {
  return postJson<unknown>(endpoint);
}
