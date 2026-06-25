import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { getResubmissions } from "../api/client";
import { formatTimestamp } from "../lib/formatDate";

const PAGE_SIZE = 20;

export function ResubmissionLog() {
  const [page, setPage] = useState(0);

  const { data, isLoading, isError, isFetching } = useQuery({
    queryKey: ["resubmissions", page],
    queryFn: () => getResubmissions(PAGE_SIZE, page * PAGE_SIZE),
    placeholderData: keepPreviousData,
    refetchInterval: page === 0 ? 30_000 : false,
  });

  if (isLoading) {
    return <p>Loading resubmission log…</p>;
  }

  if (isError) {
    return <p className="text-error">Failed to load resubmission log</p>;
  }

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  if (items.length === 0 && page > 0) {
    setPage(0);
    return null;
  }

  if (items.length === 0) {
    return <p>No resubmissions yet</p>;
  }

  return (
    <div className={isFetching ? "opacity-60 transition-opacity" : "transition-opacity"}>
      <ul className="divide-y divide-base-300">
        {items.map((item) => (
          <li key={item.id} className="flex items-center justify-between gap-4 py-2">
            <span className={`badge ${item.success ? "badge-success" : "badge-error"}`}>
              {item.success ? "Success" : "Failed"}
            </span>
            <time className="text-sm opacity-60" dateTime={item.submitted_at}>
              {formatTimestamp(item.submitted_at)}
            </time>
          </li>
        ))}
      </ul>

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
