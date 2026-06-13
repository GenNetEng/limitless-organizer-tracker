import { useQuery } from "@tanstack/react-query";
import { getResubmissions } from "../api/client";

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
    <ul className="divide-y divide-gray-200">
      {items.map((item) => (
        <li key={item.id} className="flex items-center justify-between gap-4 py-2">
          <span className={item.success ? "font-medium text-green-600" : "font-medium text-red-600"}>
            {item.success ? "Success" : "Failed"}
          </span>
          <time className="text-sm text-gray-400" dateTime={item.submitted_at}>
            {new Date(item.submitted_at).toLocaleString()}
          </time>
        </li>
      ))}
    </ul>
  );
}
