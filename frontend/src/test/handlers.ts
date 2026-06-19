import { http, HttpResponse } from "msw";

export const statusHistoryPage = {
  items: [
    {
      id: 3,
      checked_at: "2026-06-12T12:00:00Z",
      status: "rejected",
      raw_text: "check 3",
      review_note: "Your application was rejected. Please join the Discord.",
    },
    { id: 2, checked_at: "2026-06-12T10:00:00Z", status: "pending", raw_text: "check 2", review_note: null },
    { id: 1, checked_at: "2026-06-12T06:00:00Z", status: "approved", raw_text: "check 1", review_note: null },
  ],
  total: 3,
  limit: 50,
  offset: 0,
};

export const resubmissionsPage = {
  items: [
    { id: 2, submitted_at: "2026-06-12T09:00:00Z", success: true, discord_notified: true },
    { id: 1, submitted_at: "2026-06-12T08:00:00Z", success: false, discord_notified: false },
  ],
  total: 2,
  limit: 50,
  offset: 0,
};

export const games = ["POCKET", "PTCG"];

export const organizerActivityByWeek = [
  { period: "2026-06-01", count: 2 },
  { period: "2026-06-08", count: 1 },
];

export const organizerActivityForPTCG = [{ period: "2026-06-01", count: 1 }];

export const waitEstimate = {
  organizer_id: 400,
  slope: 0.5,
  intercept: 739000,
  r_squared: 0.95,
  projected_active_date: "2026-04-01",
  sample_size: 3,
  frontier_size: 2,
  points: [
    { organizer_id: 100, first_tournament_date: "2026-01-01", is_frontier: true },
    { organizer_id: 200, first_tournament_date: "2026-02-01", is_frontier: false },
    { organizer_id: 300, first_tournament_date: "2026-03-03", is_frontier: true },
  ],
};

export const organizerProfile = {
  organizer_id: 42,
  name: "Test Organizer",
  upcoming_tournaments: [
    { tournament_id: "t1", name: "Upcoming Cup", date: "2026-07-01", game: "POCKET", players: 0 },
  ],
  recent_tournaments: [
    { tournament_id: "t2", name: "Recent League", date: "2026-06-01", game: "PTCG", players: 16 },
    { tournament_id: "t3", name: "Spring Open", date: "2026-05-15", game: "POCKET", players: 32 },
  ],
  onboarded_at: "2026-05-01",
  first_tournament_date: "2026-05-15",
};

export const highestOrganizerId = { organizer_id: 2720 };

export const handlers = [
  http.get("*/api/status-history", ({ request }) => {
    const url = new URL(request.url);
    const limit = Number(url.searchParams.get("limit") ?? 50);
    const offset = Number(url.searchParams.get("offset") ?? 0);
    const sliced = statusHistoryPage.items.slice(offset, offset + limit);
    return HttpResponse.json({
      items: sliced,
      total: statusHistoryPage.items.length,
      limit,
      offset,
    });
  }),
  http.get("*/api/resubmissions", () => HttpResponse.json(resubmissionsPage)),
  http.get("*/api/games", () => HttpResponse.json(games)),
  http.get("*/api/organizers/activity", ({ request }) => {
    const game = new URL(request.url).searchParams.get("game");
    return HttpResponse.json(game === "PTCG" ? organizerActivityForPTCG : organizerActivityByWeek);
  }),
  http.get("*/api/organizers/wait-estimate", ({ request }) => {
    const organizerId = new URL(request.url).searchParams.get("organizer_id");
    const response = organizerId
      ? waitEstimate
      : { ...waitEstimate, organizer_id: null, projected_active_date: null };
    return HttpResponse.json(response);
  }),
  http.get("*/api/organizers/highest-id", () => HttpResponse.json(highestOrganizerId)),
  http.get("*/api/organizers/:organizerId/scrape", ({ params }) => {
    const id = Number(params.organizerId);
    if (id === 9999) {
      return HttpResponse.json({ detail: "organizer not found on Limitless" }, { status: 404 });
    }
    return HttpResponse.json({ ...organizerProfile, organizer_id: id });
  }),
];
