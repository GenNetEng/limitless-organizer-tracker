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
import { ApiError, getWaitEstimate, type WaitEstimate } from "../api/client";
import { toFittedLineData, toFrontierScatterData, toScatterData } from "../lib/waitEstimateChartData";

export function WaitTimeEstimator() {
  const [organizerIdInput, setOrganizerIdInput] = useState("");
  const [targetOrganizerId, setTargetOrganizerId] = useState<number | undefined>(undefined);

  const estimateQuery = useQuery<WaitEstimate, Error>({
    queryKey: ["wait-estimate", targetOrganizerId],
    queryFn: () => getWaitEstimate(targetOrganizerId),
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const parsed = Number(organizerIdInput.trim());
    if (organizerIdInput.trim() === "" || !Number.isFinite(parsed)) {
      return;
    }
    setTargetOrganizerId(parsed);
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="mb-4 flex flex-wrap items-end gap-2">
        <div>
          <label htmlFor="wait-estimate-organizer-id" className="block text-sm font-medium">
            Organizer ID (optional — enter yours for a projected date)
          </label>
          <input
            id="wait-estimate-organizer-id"
            type="number"
            value={organizerIdInput}
            onChange={(event) => setOrganizerIdInput(event.target.value)}
            className="rounded border border-gray-300 px-2 py-1"
          />
        </div>
        <button type="submit" className="rounded bg-blue-600 px-3 py-1 text-white">
          Estimate
        </button>
      </form>

      {estimateQuery.isLoading && <p>Calculating wait estimate…</p>}
      {estimateQuery.isError && (
        <p>
          {estimateQuery.error instanceof ApiError && estimateQuery.error.status === 404
            ? "Not enough data to estimate an onboarding trend."
            : "Failed to load wait estimate."}
        </p>
      )}

      {estimateQuery.data && (
        <div>
          <dl className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
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
            <div>
              <dt className="text-sm text-gray-500">Frontier organizers</dt>
              <dd className="font-semibold">{estimateQuery.data.frontier_size}</dd>
            </div>
          </dl>

          {estimateQuery.data.organizer_id !== null &&
            estimateQuery.data.projected_active_date !== null && (
              <dl className="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
                <div>
                  <dt className="text-sm text-gray-500">Projected active date</dt>
                  <dd className="font-semibold">{estimateQuery.data.projected_active_date}</dd>
                </div>
              </dl>
            )}

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
              <Scatter
                name="All organizers"
                data={toScatterData(estimateQuery.data)}
                dataKey="timestamp"
                fill="#93c5fd"
              />
              <Scatter
                name="Frontier (fastest onboarding)"
                data={toFrontierScatterData(estimateQuery.data)}
                dataKey="timestamp"
                fill="#dc2626"
              />
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
