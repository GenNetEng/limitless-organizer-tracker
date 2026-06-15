import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getGames, getOrganizerActivity } from "../api/client";
import { toActivityChartData } from "../lib/activityChartData";

export function OrganizerActivityChart() {
  const [game, setGame] = useState<string | null>(null);

  const gamesQuery = useQuery({ queryKey: ["games"], queryFn: getGames });
  const activityQuery = useQuery({
    queryKey: ["organizer-activity", game],
    queryFn: () => getOrganizerActivity(game),
  });

  const chartData = toActivityChartData(activityQuery.data ?? []);

  return (
    <div>
      <label htmlFor="activity-game-filter" className="mr-2 text-sm font-medium">
        Game
      </label>
      <select
        id="activity-game-filter"
        value={game ?? ""}
        onChange={(event) => setGame(event.target.value || null)}
        className="mb-4 rounded border border-gray-300 px-2 py-1"
      >
        <option value="">All</option>
        {(gamesQuery.data ?? []).map((g) => (
          <option key={g} value={g}>
            {g}
          </option>
        ))}
      </select>

      {activityQuery.isLoading && <p>Loading organizer activity…</p>}
      {activityQuery.isError && <p>Failed to load organizer activity.</p>}
      {activityQuery.data && chartData.length === 0 && <p>No organizer activity yet.</p>}

      {chartData.length > 0 && (
        <>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" name="New organizers" fill="#60a5fa" />
              <Line dataKey="count" name="Trend" type="monotone" stroke="#1d4ed8" dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
          {/* Accessible text alternative to the chart, also used to drive tests. */}
          <ul className="sr-only">
            {chartData.map((datum) => (
              <li key={datum.period}>
                {datum.label}: {datum.count}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
