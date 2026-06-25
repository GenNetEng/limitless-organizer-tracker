import { useQuery } from "@tanstack/react-query";
import { getOnboardingDelta } from "../api/client";

export function OnboardingDelta() {
  const query = useQuery({
    queryKey: ["onboarding-delta"],
    queryFn: getOnboardingDelta,
  });

  if (query.isLoading) return <p>Loading onboarding delta…</p>;
  if (query.isError) return <p className="text-error">Failed to load onboarding delta</p>;
  if (!query.data) return null;

  const { avg_days, median_days, count } = query.data;

  if (count === 0) {
    return <p className="text-base-content/60">No organizers with both onboarding and tournament dates yet</p>;
  }

  return (
    <div>
      <div className="flex flex-wrap gap-6">
        <div>
          <div className="text-2xl font-bold">{avg_days.toFixed(1)}</div>
          <div className="text-sm text-base-content/60">Avg days</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{median_days.toFixed(1)}</div>
          <div className="text-sm text-base-content/60">Median days</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{count}</div>
          <div className="text-sm text-base-content/60">{count === 1 ? "organizer" : "organizers"}</div>
        </div>
      </div>
      <p className="mt-2 text-xs text-base-content/50">
        Based on organizers with ID ≥ 2723 that have both an onboarding date and a first tournament date
      </p>
    </div>
  );
}
