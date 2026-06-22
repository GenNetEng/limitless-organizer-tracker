import { useQuery } from "@tanstack/react-query";
import { getAdminConfig } from "../api/client";

const CONFIG_LABELS: Record<string, string> = {
  application_status_check_interval_hours: "Status Check Interval (hours)",
  resubmit_times_utc: "Resubmit Times (UTC)",
  tournament_ingest_interval_hours: "Tournament Ingest Interval (hours)",
  tournament_ingest_limit: "Tournament Ingest Limit",
  tournament_backfill_months: "Backfill Months",
  organizer_scan_interval_hours: "Organizer Scan Interval (hours)",
  organizer_scan_limit: "Organizer Scan Limit",
};

export function AdminConfig() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin", "config"],
    queryFn: getAdminConfig,
  });

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p className="text-error">Failed to load configuration</p>;
  if (!data) return null;

  const entries = Object.entries(data) as [string, string | number][];

  return (
    <div className="overflow-x-auto">
      <table className="table table-sm w-full">
        <thead>
          <tr>
            <th>Setting</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([key, value]) => (
            <tr key={key}>
              <td>{CONFIG_LABELS[key] ?? key}</td>
              <td>{String(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
