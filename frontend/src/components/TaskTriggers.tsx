import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { getTaskTriggers, triggerTask } from "../api/client";

export function TaskTriggers() {
  const queryClient = useQueryClient();
  const { data: tasks, isLoading, error } = useQuery({
    queryKey: ["admin", "tasks"],
    queryFn: getTaskTriggers,
  });

  const [lastTriggered, setLastTriggered] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (endpoint: string) => triggerTask(endpoint),
    onSuccess: (_data, endpoint) => {
      setLastTriggered(endpoint);
      queryClient.invalidateQueries({ queryKey: ["admin", "event-log"] });
    },
  });

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p className="text-error">Failed to load tasks</p>;
  if (!tasks || tasks.length === 0) return <p>No tasks available.</p>;

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <div key={task.name} className="card bg-base-200 p-4">
          <div className="flex items-center justify-between">
            <p className="font-semibold">{task.description}</p>
            <button
              type="button"
              className={`btn btn-sm ${mutation.isPending ? "btn-disabled" : "btn-primary"}`}
              disabled={mutation.isPending}
              onClick={() => mutation.mutate(task.endpoint)}
            >
              {task.name}
            </button>
          </div>
        </div>
      ))}
      {lastTriggered && (
        <p className="text-success text-sm">Task triggered successfully</p>
      )}
      {mutation.isError && (
        <p className="text-error text-sm">Failed to trigger task</p>
      )}
    </div>
  );
}
