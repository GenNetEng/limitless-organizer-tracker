import { useQuery } from "@tanstack/react-query";
import { getStatusHistory } from "../api/client";

export function StatusTimeline() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["status-history"],
    queryFn: getStatusHistory,
  });

  if (isLoading) {
    return <p>Loading status history…</p>;
  }

  if (isError) {
    return <p>Failed to load status history.</p>;
  }

  const items = data?.items ?? [];

  if (items.length === 0) {
    return <p>No status checks yet.</p>;
  }

  return (
    <ul className="divide-y divide-gray-200">
      {items.map((item) => (
        <li key={item.id} className="flex items-center justify-between gap-4 py-2">
          <span className="font-medium">{item.status}</span>
          <span className="flex-1 text-gray-500">{item.raw_text}</span>
          <time className="text-sm text-gray-400" dateTime={item.checked_at}>
            {new Date(item.checked_at).toLocaleString()}
          </time>
        </li>
      ))}
    </ul>
  );
}
