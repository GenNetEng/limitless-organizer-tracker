import { useQuery } from "@tanstack/react-query";
import { getDiagnostics } from "../api/client";
import { formatTimestamp } from "../lib/formatDate";

function HealthBadge({ ok }: { ok: boolean }) {
  return (
    <span className={`badge ${ok ? "badge-success" : "badge-error"}`}>
      {ok ? "Healthy" : "Down"}
    </span>
  );
}

export function Diagnostics() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin", "diagnostics"],
    queryFn: getDiagnostics,
  });

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p className="text-error">Failed to load diagnostics</p>;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="card bg-base-300 p-4">
          <h3 className="font-semibold">Database</h3>
          <HealthBadge ok={data.db_ok} />
        </div>
        <div className="card bg-base-300 p-4">
          <h3 className="font-semibold">Redis</h3>
          <HealthBadge ok={data.redis_ok} />
        </div>
        <div className="card bg-base-300 p-4">
          <h3 className="font-semibold">Celery Beat</h3>
          <HealthBadge ok={data.beat_ok} />
        </div>
      </div>

      <div className="card bg-base-300 p-4">
        <h3 className="mb-2 font-semibold">Celery Workers</h3>
        {data.celery_workers.length > 0 ? (
          <ul className="list-inside list-disc">
            {data.celery_workers.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        ) : (
          <p className="text-warning">No workers connected</p>
        )}
      </div>

      <div className="card bg-base-300 p-4">
        <h3 className="mb-2 font-semibold">Last Task Success</h3>
        <table className="table table-zebra table-sm w-full border border-base-content/10 [&_th]:border-b [&_th]:border-base-content/10 [&_td]:border-b [&_td]:border-base-content/10">
          <thead>
            <tr>
              <th>Task</th>
              <th>Last Success</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.last_success_per_task).map(([task, ts]) => (
              <tr key={task}>
                <td>{task}</td>
                <td>{ts ? formatTimestamp(ts) : "Never"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
