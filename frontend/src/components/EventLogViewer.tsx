import { useQuery } from "@tanstack/react-query";
import { getEventLog } from "../api/client";
import { formatTimestamp } from "../lib/formatDate";

export function EventLogViewer() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin", "event-log"],
    queryFn: () => getEventLog(),
  });

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p className="text-error">Failed to load event log</p>;
  if (!data || data.items.length === 0) return <p>No events recorded yet.</p>;

  return (
    <div className="overflow-x-auto">
      <table className="table table-zebra table-sm w-full border border-base-content/10 [&_th]:border-b [&_th]:border-base-content/10 [&_td]:border-b [&_td]:border-base-content/10">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Type</th>
            <th>Severity</th>
            <th>Source</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((entry) => (
            <tr key={entry.id}>
              <td className="whitespace-nowrap">
                {formatTimestamp(entry.timestamp)}
              </td>
              <td>{entry.event_type}</td>
              <td>
                <span
                  className={`badge badge-sm ${
                    entry.severity === "error"
                      ? "badge-error"
                      : entry.severity === "warning"
                        ? "badge-warning"
                        : "badge-info"
                  }`}
                >
                  {entry.severity}
                </span>
              </td>
              <td>{entry.source}</td>
              <td>{entry.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-sm opacity-60">
        Showing {data.items.length} of {data.total} events
      </p>
    </div>
  );
}
