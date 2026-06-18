import { useQuery } from "@tanstack/react-query";
import { getStatusHistory } from "../api/client";

const STATUS_COLORS: Record<string, string> = {
  approved: "text-green-600",
  rejected: "text-red-600",
  pending: "text-yellow-600",
  unknown: "text-gray-500",
};

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
          <span className={`font-medium ${STATUS_COLORS[item.status] ?? "text-gray-500"}`}>
            {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
          </span>
          <time className="text-sm text-gray-400" dateTime={item.checked_at}>
            {new Date(item.checked_at).toLocaleString()}
          </time>
        </li>
      ))}
    </ul>
  );
}
