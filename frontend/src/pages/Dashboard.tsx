import { HighestOrganizerIdCard } from "../components/HighestOrganizerIdCard";
import { OrganizerActivityChart } from "../components/OrganizerActivityChart";
import { OrganizerProfile } from "../components/OrganizerProfile";
import { ResubmissionLog } from "../components/ResubmissionLog";
import { StatusTimeline } from "../components/StatusTimeline";
import { WaitTimeEstimator } from "../components/WaitTimeEstimator";

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
      <section>
        <h2 className="mb-2 text-lg font-semibold">Organizer Activity</h2>
        <OrganizerActivityChart />
      </section>
      <section>
        <h2 className="mb-2 text-lg font-semibold">Wait Time Estimator</h2>
        <WaitTimeEstimator />
      </section>
      <section>
        <h2 className="mb-2 text-lg font-semibold">Highest Organizer ID</h2>
        <HighestOrganizerIdCard />
      </section>
      <section>
        <h2 className="mb-2 text-lg font-semibold">Organizer Profile</h2>
        <OrganizerProfile />
      </section>
    </main>
  );
}
