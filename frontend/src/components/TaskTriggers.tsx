import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { getTaskTriggers, triggerTask } from "../api/client";

const COMPONENT_BADGE: Record<string, string> = {
  Tournaments: "badge-info",
  Organizers: "badge-success",
  Application: "badge-warning",
};

export function TaskTriggers() {
  const queryClient = useQueryClient();
  const { data: tasks, isLoading, error } = useQuery({
    queryKey: ["admin", "tasks"],
    queryFn: getTaskTriggers,
  });

  const [lastTriggered, setLastTriggered] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (endpoint: string) => triggerTask(endpoint),
    onMutate: () => setLastTriggered(null),
    onSuccess: (_data, endpoint) => {
      setLastTriggered(endpoint);
      queryClient.invalidateQueries({ queryKey: ["admin", "event-log"] });
    },
  });

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p className="text-error">Failed to load tasks</p>;
  if (!tasks || tasks.length === 0) return <p>No tasks available</p>;

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="table table-sm w-full">
          <thead>
            <tr>
              <th>Component</th>
              <th>Task</th>
              <th className="w-16 text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.name} className="even:bg-base-300">
                <td>
                  <span className={`badge badge-sm ${COMPONENT_BADGE[task.component] ?? "badge-ghost"}`}>
                    {task.component}
                  </span>
                </td>
                <td>{task.description}</td>
                <td className="text-center">
                  <button
                    type="button"
                    aria-label={`Run ${task.description}`}
                    className={`btn btn-sm btn-circle ${mutation.isPending ? "btn-disabled" : "bg-primary text-primary-content hover:bg-primary/80"}`}
                    disabled={mutation.isPending}
                    onClick={() => mutation.mutate(task.endpoint)}
                  >
                    ▶
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {lastTriggered && (
        <p className="text-success text-sm mt-2">Task triggered successfully</p>
      )}
      {mutation.isError && (
        <p className="text-error text-sm mt-2">Failed to trigger task</p>
      )}
    </div>
  );
}
