import { useQuery } from "@tanstack/react-query";
import { ApiError, getEventLog, getHighestOrganizerId } from "../api/client";
import { formatTimestamp } from "../lib/formatDate";

export function ScannerStatusCard() {
  const highestIdQuery = useQuery({
    queryKey: ["highest-organizer-id"],
    queryFn: getHighestOrganizerId,
  });

  const scanEventQuery = useQuery({
    queryKey: ["scanner-audit-event"],
    queryFn: () => getEventLog({ event_type: "scanner.audit_complete", limit: 1 }),
  });

  if (highestIdQuery.isLoading || scanEventQuery.isLoading) {
    return <p>Loading…</p>;
  }

  if (highestIdQuery.isError) {
    if (
      highestIdQuery.error instanceof ApiError &&
      highestIdQuery.error.status === 404
    ) {
      return <p>No organizer data available yet</p>;
    }
    return <p className="text-error">Failed to load scanner status</p>;
  }

  if (scanEventQuery.isError) {
    return <p className="text-error">Failed to load scanner status</p>;
  }

  const latestScan = scanEventQuery.data?.items[0];
  const queued =
    latestScan?.details &&
    typeof latestScan.details === "object" &&
    !Array.isArray(latestScan.details)
      ? (latestScan.details as Record<string, unknown>).queued
      : undefined;

  return (
    <div className="flex flex-wrap gap-4">
      <div className="stats shadow">
        <div className="stat">
          <div className="stat-title">Scanner Watermark</div>
          <div className="stat-value text-primary">
            {highestIdQuery.data?.organizer_id}
          </div>
        </div>
      </div>

      <div className="stats shadow">
        <div className="stat">
          <div className="stat-title">Last Scan</div>
          <div className="stat-value text-sm">
            {latestScan ? (
              formatTimestamp(latestScan.timestamp)
            ) : (
              <span className="text-base-content/60">No scan data yet</span>
            )}
          </div>
        </div>
      </div>

      <div className="stats shadow">
        <div className="stat">
          <div className="stat-title">Found in Last Scan</div>
          <div className="stat-value text-accent">
            {latestScan ? (
              queued !== undefined ? (
                String(queued)
              ) : (
                <span className="text-base-content/60">—</span>
              )
            ) : (
              <span className="text-sm text-base-content/60">
                No scan data yet
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
