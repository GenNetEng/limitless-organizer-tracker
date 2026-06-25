import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { getEventLog } from "../api/client";
import { formatTimestamp } from "../lib/formatDate";

const SEVERITY_BADGE: Record<string, string> = {
  error: "badge-error",
  warning: "badge-warning",
  info: "badge-info",
  debug: "badge-ghost",
};

const PAGE_SIZE = 20;

export function EventLogViewer() {
  const [page, setPage] = useState(0);

  const { data, isLoading, error, isFetching } = useQuery({
    queryKey: ["admin", "event-log", page],
    queryFn: () => getEventLog({ limit: PAGE_SIZE, offset: page * PAGE_SIZE }),
    placeholderData: keepPreviousData,
    refetchInterval: page === 0 ? 30_000 : false,
  });

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p className="text-error">Failed to load event log</p>;

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  if (items.length === 0 && page > 0) {
    setPage(0);
    return null;
  }

  if (items.length === 0) return <p>No events recorded yet</p>;

  return (
    <div className={`overflow-x-auto ${isFetching ? "opacity-60 transition-opacity" : "transition-opacity"}`}>
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
          {items.map((entry) => (
            <tr key={entry.id}>
              <td className="whitespace-nowrap">
                {formatTimestamp(entry.timestamp)}
              </td>
              <td>{entry.event_type}</td>
              <td>
                <span className={`badge badge-sm ${SEVERITY_BADGE[entry.severity.toLowerCase()] ?? "badge-ghost"}`}>
                  {entry.severity}
                </span>
              </td>
              <td>{entry.source}</td>
              <td>{entry.message}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages <= 1 && total > 0 && (
        <p className="mt-2 text-sm opacity-60">{total} events</p>
      )}

      {totalPages > 1 && (
        <div className="mt-3 flex items-center justify-between text-sm">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="btn btn-sm btn-ghost"
          >
            « Previous
          </button>
          <span className="opacity-60">
            Page {page + 1} of {totalPages} · {total} total
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="btn btn-sm btn-ghost"
          >
            Next »
          </button>
        </div>
      )}
    </div>
  );
}
