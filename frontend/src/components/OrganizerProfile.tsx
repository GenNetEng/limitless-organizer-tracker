import { useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { ApiError, scrapeOrganizerProfile, type TournamentEntry } from "../api/client";

function TournamentList({ tournaments, label }: { tournaments: TournamentEntry[]; label: string }) {
  if (tournaments.length === 0) {
    return <p className="text-sm text-gray-500">No {label.toLowerCase()}.</p>;
  }

  return (
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
  );
}

export function OrganizerProfile() {
  const [idInput, setIdInput] = useState("");
  const [organizerId, setOrganizerId] = useState<number | undefined>(undefined);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["organizer-profile", organizerId],
    queryFn: () => scrapeOrganizerProfile(organizerId!),
    enabled: organizerId !== undefined,
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

          <div>
            <h4 className="mb-1 text-sm font-medium text-gray-700">Upcoming Tournaments</h4>
            <TournamentList tournaments={data.upcoming_tournaments} label="Upcoming Tournaments" />
          </div>

          <div>
            <h4 className="mb-1 text-sm font-medium text-gray-700">Recent Tournaments</h4>
            <TournamentList tournaments={data.recent_tournaments} label="Recent Tournaments" />
          </div>
        </div>
      )}
    </div>
  );
}
