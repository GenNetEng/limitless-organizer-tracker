import { http, HttpResponse } from "msw";

export const statusHistoryPage = {
  items: [
    { id: 2, checked_at: "2026-06-12T10:00:00Z", status: "pending", raw_text: "check 2" },
    { id: 1, checked_at: "2026-06-12T06:00:00Z", status: "approved", raw_text: "check 1" },
  ],
  total: 2,
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
  game: "PTCG",
  slope: 0.5,
  intercept: 739000,
  r_squared: 0.95,
  projected_active_date: "2026-04-01",
  sample_size: 3,
  points: [
    { organizer_id: 100, first_tournament_date: "2026-01-01" },
    { organizer_id: 200, first_tournament_date: "2026-02-01" },
    { organizer_id: 300, first_tournament_date: "2026-03-03" },
  ],
};

export const handlers = [
  http.get("*/api/status-history", () => HttpResponse.json(statusHistoryPage)),
  http.get("*/api/resubmissions", () => HttpResponse.json(resubmissionsPage)),
  http.get("*/api/games", () => HttpResponse.json(games)),
  http.get("*/api/organizers/activity", ({ request }) => {
    const game = new URL(request.url).searchParams.get("game");
    return HttpResponse.json(game === "PTCG" ? organizerActivityForPTCG : organizerActivityByWeek);
  }),
  http.get("*/api/organizers/wait-estimate", () => HttpResponse.json(waitEstimate)),
];
