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
import { filterByDateWindow, type DateWindow } from "../lib/dateWindow";
import { DateWindowSelect } from "./DateWindowSelect";

export function OrganizerActivityChart() {
  const [game, setGame] = useState<string | null>(null);
  const [dateWindow, setDateWindow] = useState<DateWindow>("");

  const gamesQuery = useQuery({ queryKey: ["games"], queryFn: getGames });
  const activityQuery = useQuery({
    queryKey: ["organizer-activity", game],
    queryFn: () => getOrganizerActivity(game),
  });

  const filtered = filterByDateWindow(activityQuery.data ?? [], (b) => b.period, dateWindow);
  const chartData = toActivityChartData(filtered);

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end gap-4">
        <div className="form-control w-fit">
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
        <DateWindowSelect id="activity-date-range" value={dateWindow} onChange={setDateWindow} />
      </div>

      {activityQuery.isLoading && <p>Loading organizer activity…</p>}
      {activityQuery.isError && <p className="text-error">Failed to load organizer activity</p>}
      {activityQuery.data && chartData.length === 0 && (
        <p>{dateWindow ? "No activity in the selected date range" : "No organizer activity yet"}</p>
      )}

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
