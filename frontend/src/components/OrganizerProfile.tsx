import { useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { ApiError, scrapeOrganizerProfile, type TournamentEntry } from "../api/client";

function TournamentList({ tournaments, label }: { tournaments: TournamentEntry[]; label: string }) {
  return (
    <div>
      <h4 className="mb-1 text-sm font-medium text-gray-700">{label}</h4>
      {tournaments.length === 0 ? (
        <p className="text-sm text-gray-500">No {label.toLowerCase()}.</p>
      ) : (
        <ul className="divide-y divide-gray-200">
          {tournaments.map((t) => (
            <li key={t.tournament_id} className="py-2">
              <div className="flex items-center justify-between gap-4">
                <span className="font-medium">{t.name}</span>
                <span className="text-sm text-gray-400">{t.date}</span>
              </div>
              <p className="text-sm text-gray-500">
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
        <div>
          <label htmlFor="organizer-profile-id" className="block text-sm font-medium">
            Organizer ID
          </label>
          <input
            id="organizer-profile-id"
            type="number"
            min="1"
            value={idInput}
            onChange={(e) => setIdInput(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1"
          />
        </div>
        <button type="submit" className="rounded bg-blue-600 px-3 py-1 text-white">
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
          <h3 className="text-lg font-semibold">{data.name}</h3>

          {(data.onboarded_at || data.first_tournament_date) && (
            <dl className="grid grid-cols-2 gap-2">
              {data.onboarded_at && (
                <div>
                  <dt className="text-sm text-gray-500">Onboarded</dt>
                  <dd className="font-semibold">{data.onboarded_at}</dd>
                </div>
              )}
              {data.first_tournament_date && (
                <div>
                  <dt className="text-sm text-gray-500">First Tournament</dt>
                  <dd className="font-semibold">{data.first_tournament_date}</dd>
                </div>
              )}
            </dl>
          )}

          <TournamentList tournaments={data.upcoming_tournaments} label="Upcoming Tournaments" />
          <TournamentList tournaments={data.recent_tournaments} label="Recent Tournaments" />
        </div>
      )}
    </div>
  );
}
