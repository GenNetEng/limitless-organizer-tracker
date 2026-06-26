import { useQuery } from "@tanstack/react-query";
import { getResubmissions, getStatusHistory } from "../api/client";
import { formatTimestamp } from "../lib/formatDate";
import { STATUS_COLORS } from "../lib/statusColors";

export function ApplicationStatCards() {
  const statusQuery = useQuery({
    queryKey: ["status-history", 1, 0],
    queryFn: () => getStatusHistory(1, 0),
  });

  const resubQuery = useQuery({
    queryKey: ["resubmissions-summary"],
    queryFn: () => getResubmissions(1, 0),
  });

  if (statusQuery.isLoading || resubQuery.isLoading) {
    return <p>Loading…</p>;
  }

  if (statusQuery.isError || resubQuery.isError) {
    return <p className="text-error">Failed to load application stats</p>;
  }

  const latestStatus = statusQuery.data?.items[0];
  const resubTotal = resubQuery.data?.total ?? 0;
  const latestResub = resubQuery.data?.items[0];

  return (
    <div className="flex flex-wrap gap-4">
      <div className="stats shadow">
        <div className="stat">
          <div className="stat-title">Current Status</div>
          <div className="stat-value">
            {latestStatus ? (
              <span
                className={`badge ${STATUS_COLORS[latestStatus.status] ?? "badge-ghost"}`}
              >
                {latestStatus.status.charAt(0).toUpperCase() +
                  latestStatus.status.slice(1)}
              </span>
            ) : (
              <span className="text-sm text-base-content/60">
                No status checks yet
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="stats shadow">
        <div className="stat">
          <div className="stat-title">Last Check</div>
          <div className="stat-value text-sm">
            {latestStatus ? (
              formatTimestamp(latestStatus.checked_at)
            ) : (
              <span className="text-base-content/60">—</span>
            )}
          </div>
        </div>
      </div>

      <div className="stats shadow">
        <div className="stat">
          <div className="stat-title">Total Resubmissions</div>
          <div className="stat-value text-primary">
            {resubTotal > 0 ? (
              resubTotal
            ) : (
              <span className="text-sm text-base-content/60">
                No resubmissions yet
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="stats shadow">
        <div className="stat">
          <div className="stat-title">Last Resubmission</div>
          <div className="stat-value text-sm">
            {latestResub ? (
              formatTimestamp(latestResub.submitted_at)
            ) : (
              <span className="text-base-content/60">—</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
