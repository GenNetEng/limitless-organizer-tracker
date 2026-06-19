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
      <div className="form-control mb-4 w-fit">
        <label htmlFor="activity-game-filter" className="label">
          <span className="label-text">Game</span>
        </label>
        <select
          id="activity-game-filter"
          value={game ?? ""}
          onChange={(event) => setGame(event.target.value || null)}
          className="select select-bordered select-sm"
        >
          <option value="">All</option>
          {(gamesQuery.data ?? []).map((g) => (
            <option key={g} value={g}>
              {g}
            </option>
          ))}
        </select>
      </div>

      {activityQuery.isLoading && <p>Loading organizer activity…</p>}
      {activityQuery.isError && <p>Failed to load organizer activity.</p>}
      {activityQuery.data && chartData.length === 0 && <p>No organizer activity yet.</p>}

      {chartData.length > 0 && (
        <>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="label" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" name="New organizers" fill="#75d1f0" />
              <Line dataKey="count" name="Trend" type="monotone" stroke="#ff7598" dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
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
