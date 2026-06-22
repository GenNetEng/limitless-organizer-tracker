import { useQuery } from "@tanstack/react-query";
import { getResubmissions } from "../api/client";
import { formatTimestamp } from "../lib/formatDate";

export function ResubmissionLog() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["resubmissions"],
    queryFn: getResubmissions,
  });

  if (isLoading) {
    return <p>Loading resubmission log…</p>;
  }

  if (isError) {
    return <p>Failed to load resubmission log.</p>;
  }

  const items = data?.items ?? [];

  if (items.length === 0) {
    return <p>No resubmissions yet.</p>;
  }

  return (
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
  );
}
