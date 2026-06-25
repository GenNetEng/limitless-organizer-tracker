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
      return <p>No organizer data available yet</p>;
    }
    return <p className="text-error">Failed to load highest organizer ID</p>;
  }

  return (
    <div className="stats shadow">
      <div className="stat">
        <div className="stat-title">Highest Organizer ID</div>
        <div className="stat-value text-primary">{data?.organizer_id}</div>
      </div>
    </div>
  );
}
