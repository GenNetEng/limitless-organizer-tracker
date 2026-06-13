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

export const handlers = [
  http.get("*/api/status-history", () => HttpResponse.json(statusHistoryPage)),
  http.get("*/api/resubmissions", () => HttpResponse.json(resubmissionsPage)),
];
