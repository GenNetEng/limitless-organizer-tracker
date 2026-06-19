import { useQuery } from "@tanstack/react-query";
import { ApiError, getHighestOrganizerId } from "../api/client";

export function HighestOrganizerIdCard() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["highest-organizer-id"],
    queryFn: getHighestOrganizerId,
  });

  if (isLoading) {
    return <p>Loading highest organizer ID…</p>;
  }

  if (isError) {
    if (error instanceof ApiError && error.status === 404) {
      return <p>No organizer data available yet.</p>;
    }
    return <p>Failed to load highest organizer ID.</p>;
  }

  return (
    <dl className="rounded-lg border border-gray-200 p-4">
      <dt className="text-sm text-gray-500">Highest Organizer ID</dt>
      <dd className="text-3xl font-bold">{data?.organizer_id}</dd>
    </dl>
  );
}
