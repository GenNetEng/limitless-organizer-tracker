import { ResubmissionLog } from "../components/ResubmissionLog";
import { StatusTimeline } from "../components/StatusTimeline";

export function Dashboard() {
  return (
    <main className="mx-auto max-w-3xl space-y-8 p-6">
      <h1 className="text-2xl font-bold">Limitless Organizer Tracker</h1>
      <section>
        <h2 className="mb-2 text-lg font-semibold">Status History</h2>
        <StatusTimeline />
      </section>
      <section>
        <h2 className="mb-2 text-lg font-semibold">Resubmission Log</h2>
        <ResubmissionLog />
      </section>
    </main>
  );
}
