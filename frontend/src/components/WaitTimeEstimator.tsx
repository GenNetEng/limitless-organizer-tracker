import { useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getGames, getWaitEstimate, type WaitEstimate } from "../api/client";
import { toFittedLineData, toScatterData } from "../lib/waitEstimateChartData";

interface EstimateQuery {
  organizerId: number;
  game: string;
}

function fetchEstimate(query: EstimateQuery | null): Promise<WaitEstimate> {
  if (query === null) {
    return Promise.reject(new Error("no organizer ID / game selected"));
  }
  return getWaitEstimate(query.organizerId, query.game);
}

export function WaitTimeEstimator() {
  const [organizerIdInput, setOrganizerIdInput] = useState("");
  const [game, setGame] = useState("");
  const [query, setQuery] = useState<EstimateQuery | null>(null);

  const gamesQuery = useQuery({ queryKey: ["games"], queryFn: getGames });
  const estimateQuery = useQuery({
    queryKey: ["wait-estimate", query],
    queryFn: () => fetchEstimate(query),
    enabled: query !== null,
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const organizerId = Number(organizerIdInput);
    if (!game || organizerIdInput.trim() === "" || !Number.isFinite(organizerId)) {
      return;
    }
    setQuery({ organizerId, game });
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="mb-4 flex flex-wrap items-end gap-2">
        <div>
          <label htmlFor="wait-estimate-organizer-id" className="block text-sm font-medium">
            Organizer ID
          </label>
          <input
            id="wait-estimate-organizer-id"
            type="number"
            value={organizerIdInput}
            onChange={(event) => setOrganizerIdInput(event.target.value)}
            className="rounded border border-gray-300 px-2 py-1"
          />
        </div>
        <div>
          <label htmlFor="wait-estimate-game" className="block text-sm font-medium">
            Game
          </label>
          <select
            id="wait-estimate-game"
            value={game}
            onChange={(event) => setGame(event.target.value)}
            className="rounded border border-gray-300 px-2 py-1"
          >
            <option value="">Select a game</option>
            {(gamesQuery.data ?? []).map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </div>
        <button type="submit" className="rounded bg-blue-600 px-3 py-1 text-white">
          Estimate
        </button>
      </form>

      {estimateQuery.isLoading && <p>Calculating wait estimate…</p>}
      {estimateQuery.isError && <p>Not enough data to estimate a wait time for this game.</p>}

      {estimateQuery.data && (
        <div>
          <dl className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <div>
              <dt className="text-sm text-gray-500">Projected active date</dt>
              <dd className="font-semibold">{estimateQuery.data.projected_active_date}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Slope (days / organizer ID)</dt>
              <dd className="font-semibold">{estimateQuery.data.slope.toFixed(4)}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">R²</dt>
              <dd className="font-semibold">{estimateQuery.data.r_squared.toFixed(3)}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Sample size</dt>
              <dd className="font-semibold">{estimateQuery.data.sample_size}</dd>
            </div>
          </dl>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="organizerId" type="number" name="Organizer ID" domain={["auto", "auto"]} />
              <YAxis
                dataKey="timestamp"
                type="number"
                name="First tournament date"
                domain={["auto", "auto"]}
                tickFormatter={(value: number) => new Date(value).toLocaleDateString()}
              />
              <Tooltip />
              <Scatter name="Organizers" data={toScatterData(estimateQuery.data)} dataKey="timestamp" fill="#1d4ed8" />
              <Line
                name="Fitted line"
                data={toFittedLineData(estimateQuery.data)}
                dataKey="timestamp"
                stroke="#f97316"
                dot={false}
                type="linear"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
