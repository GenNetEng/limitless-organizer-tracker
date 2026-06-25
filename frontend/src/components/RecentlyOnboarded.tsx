import { useQuery } from "@tanstack/react-query";
import { getRecentlyOnboarded } from "../api/client";
import { formatDateShort, formatTimestamp } from "../lib/formatDate";

export function RecentlyOnboarded() {
  const query = useQuery({
    queryKey: ["recently-onboarded"],
    queryFn: () => getRecentlyOnboarded(),
  });

  if (query.isLoading) return <p>Loading recently onboarded organizers…</p>;
  if (query.isError) return <p className="text-error">Failed to load recently onboarded organizers</p>;
  if (query.data && query.data.length === 0) return <p>No recently onboarded organizers yet</p>;

  return (
    <div className="overflow-x-auto">
      <table className="table table-sm w-full">
        <thead>
          <tr>
            <th>Organizer ID</th>
            <th>Detected</th>
            <th>Onboarded</th>
            <th>First Tournament</th>
          </tr>
        </thead>
        <tbody>
          {query.data?.map((org) => (
            <tr key={org.organizer_id} className="even:bg-base-200">
              <td>
                <a
                  href={`https://play.limitlesstcg.com/organizer/${org.organizer_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link link-primary"
                >
                  {org.organizer_id}
                </a>
              </td>
              <td>{org.detected_at ? formatTimestamp(org.detected_at) : "—"}</td>
              <td>{org.onboarded_at ? formatDateShort(org.onboarded_at) : "—"}</td>
              <td>{org.first_tournament_date ? formatDateShort(org.first_tournament_date) : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
