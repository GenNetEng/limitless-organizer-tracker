import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getAdminConfig, updateAdminConfig } from "../api/client";
import type { AdminConfig as AdminConfigType } from "../api/client";

const CONFIG_LABELS: Record<string, string> = {
  application_status_check_interval_hours: "Status Check Interval (hours)",
  resubmit_times_utc: "Resubmit Times (UTC)",
  tournament_ingest_interval_hours: "Tournament Ingest Interval (hours)",
  tournament_ingest_limit: "Tournament Ingest Limit",
  tournament_backfill_months: "Backfill Months",
  organizer_scan_interval_hours: "Organizer Scan Interval (hours)",
  organizer_scan_limit: "Organizer Scan Limit",
  organizer_scan_start_id: "Organizer Scan Start ID",
};

export function AdminConfig() {
  const queryClient = useQueryClient();
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin", "config"],
    queryFn: getAdminConfig,
  });

  const mutation = useMutation({
    mutationFn: updateAdminConfig,
    onSuccess: (updated) => {
      queryClient.setQueryData(["admin", "config"], updated);
      setEditingKey(null);
      setSaveError(null);
    },
    onError: (err: Error) => {
      setSaveError(err.message || "Save failed");
    },
  });

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p className="text-error">Failed to load configuration</p>;
  if (!data) return null;

  const keys = Object.keys(CONFIG_LABELS) as (keyof typeof CONFIG_LABELS)[];

  function handleEdit(key: string) {
    setEditingKey(key);
    setEditValue(String(data![key as keyof AdminConfigType]));
    setSaveError(null);
  }

  function handleCancel() {
    setEditingKey(null);
    setEditValue("");
    setSaveError(null);
  }

  function handleSave() {
    if (!editingKey) return;
    mutation.mutate({ [editingKey]: editValue });
  }

  return (
    <div className="overflow-x-auto">
      <table className="table table-sm w-full border border-base-content/10 [&_th]:border-b [&_th]:border-base-content/10 [&_td]:border-b [&_td]:border-base-content/10">
        <thead>
          <tr>
            <th>Setting</th>
            <th>Value</th>
            <th className="w-24">Actions</th>
          </tr>
        </thead>
        <tbody>
          {keys.map((key) => (
            <tr key={key}>
              <td>{CONFIG_LABELS[key]}</td>
              <td>
                {editingKey === key ? (
                  <input
                    type="text"
                    className="input input-sm input-bordered w-full"
                    aria-label={CONFIG_LABELS[key]}
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                  />
                ) : (
                  String(data[key as keyof AdminConfigType])
                )}
              </td>
              <td>
                {editingKey === key ? (
                  <span className="flex gap-1">
                    <button
                      type="button"
                      className="btn btn-xs btn-success"
                      onClick={handleSave}
                      disabled={mutation.isPending}
                    >
                      Save
                    </button>
                    <button
                      type="button"
                      className="btn btn-xs btn-ghost"
                      onClick={handleCancel}
                      disabled={mutation.isPending}
                    >
                      Cancel
                    </button>
                  </span>
                ) : (
                  <button
                    type="button"
                    className="btn btn-xs btn-ghost"
                    onClick={() => handleEdit(key)}
                    disabled={editingKey !== null}
                  >
                    Edit
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {saveError && <p className="text-error text-sm mt-2">{saveError}</p>}
    </div>
  );
}
