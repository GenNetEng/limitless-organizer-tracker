import { useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { ApiError, scrapeOrganizerProfile, type TournamentEntry } from "../api/client";

function TournamentList({ tournaments, label }: { tournaments: TournamentEntry[]; label: string }) {
  return (
    <div>
      <h4 className="mb-1 text-sm font-medium opacity-70">{label}</h4>
      {tournaments.length === 0 ? (
        <p className="text-sm opacity-50">No {label.toLowerCase()}.</p>
      ) : (
        <ul className="divide-y divide-base-300">
          {tournaments.map((t) => (
            <li key={t.tournament_id} className="py-2">
              <div className="flex items-center justify-between gap-4">
                <span className="font-medium">{t.name}</span>
                <span className="text-sm opacity-60">{t.date}</span>
              </div>
              <p className="text-sm opacity-50">
                {t.game} · {t.players} players
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function OrganizerProfile() {
  const [idInput, setIdInput] = useState("");
  const [organizerId, setOrganizerId] = useState<number | undefined>(undefined);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["organizer-profile", organizerId],
    queryFn: () => scrapeOrganizerProfile(organizerId!),
    enabled: organizerId !== undefined,
    staleTime: 60_000,
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const parsed = Number(idInput.trim());
    if (!Number.isFinite(parsed) || parsed < 1) {
      return;
    }
    setOrganizerId(parsed);
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="mb-4 flex flex-wrap items-end gap-2">
        <div className="form-control">
          <label htmlFor="organizer-profile-id" className="label">
            <span className="label-text">Organizer ID</span>
          </label>
          <input
            id="organizer-profile-id"
            type="number"
            min="1"
            value={idInput}
            onChange={(e) => setIdInput(e.target.value)}
            className="input input-bordered input-sm w-32"
          />
        </div>
        <button type="submit" className="btn btn-primary btn-sm">
          Look Up
        </button>
      </form>

      {isLoading && <p>Loading organizer profile…</p>}

      {isError && (
        <p>
          {error instanceof ApiError && error.status === 404
            ? "Organizer not found."
            : "Failed to load organizer profile."}
        </p>
      )}

      {data && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-secondary">{data.name}</h3>

          {(data.onboarded_at || data.estimated_onboard_date || data.first_tournament_date) && (
            <div className="stats stats-horizontal shadow">
              {data.onboarded_at && (
                <div className="stat">
                  <div className="stat-title">Onboarded</div>
                  <div className="stat-value text-sm">{data.onboarded_at}</div>
                </div>
              )}
              {!data.onboarded_at && data.estimated_onboard_date && (
                <div className="stat">
                  <div className="stat-title">Est. Onboarded</div>
                  <div className="stat-value text-sm">{data.estimated_onboard_date}</div>
                </div>
              )}
              {data.first_tournament_date && (
                <div className="stat">
                  <div className="stat-title">First Tournament</div>
                  <div className="stat-value text-sm">{data.first_tournament_date}</div>
                </div>
              )}
            </div>
          )}

          <TournamentList tournaments={data.upcoming_tournaments} label="Upcoming Tournaments" />
          <TournamentList tournaments={data.recent_tournaments} label="Recent Tournaments" />
        </div>
      )}
    </div>
  );
}
