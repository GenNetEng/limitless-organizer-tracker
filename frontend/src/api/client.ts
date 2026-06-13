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
