import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getStatusHistory } from "../api/client";
import { formatTimestamp } from "../lib/formatDate";

const STATUS_COLORS: Record<string, string> = {
  approved: "badge-success",
  rejected: "badge-error",
  pending: "badge-warning",
  expired: "badge-ghost",
  unknown: "badge-ghost",
};

const PAGE_SIZE = 20;

export function StatusTimeline() {
  const [page, setPage] = useState(0);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["status-history", page],
    queryFn: () => getStatusHistory(PAGE_SIZE, page * PAGE_SIZE),
  });

  if (isLoading) {
    return <p>Loading status history…</p>;
  }

  if (isError) {
    return <p>Failed to load status history.</p>;
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  if (items.length === 0 && page === 0) {
    return <p>No status checks yet.</p>;
  }

  return (
    <div>
      <div className="max-h-96 overflow-y-auto">
        <ul className="divide-y divide-base-300">
          {items.map((item) => (
            <li key={item.id} className="py-2">
              <div className="flex items-center justify-between gap-4">
                <span className={`badge ${STATUS_COLORS[item.status] ?? "badge-ghost"}`}>
                  {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                </span>
                <time className="text-sm opacity-60" dateTime={item.checked_at}>
                  {formatTimestamp(item.checked_at)}
                </time>
              </div>
              {item.review_note && (
                <p className="mt-1 text-sm opacity-70">{item.review_note}</p>
              )}
            </li>
          ))}
        </ul>
      </div>

      {totalPages > 1 && (
        <div className="mt-3 flex items-center justify-between text-sm">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="btn btn-sm btn-ghost"
          >
            Previous
          </button>
          <span className="opacity-60">
            Page {page + 1} of {totalPages} ({total} total)
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="btn btn-sm btn-ghost"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
