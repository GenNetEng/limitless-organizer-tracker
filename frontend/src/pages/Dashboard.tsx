import { useState } from "react";
import { AdminConfig } from "../components/AdminConfig";
import { Diagnostics } from "../components/Diagnostics";
import { EventLogViewer } from "../components/EventLogViewer";
import { HighestOrganizerIdCard } from "../components/HighestOrganizerIdCard";
import { OrganizerActivityChart } from "../components/OrganizerActivityChart";
import { OrganizerProfile } from "../components/OrganizerProfile";
import { ResubmissionLog } from "../components/ResubmissionLog";
import { StatusTimeline } from "../components/StatusTimeline";
import { TabNavigation, type Tab } from "../components/TabNavigation";
import { TaskTriggers } from "../components/TaskTriggers";
import { WaitTimeEstimator } from "../components/WaitTimeEstimator";

const TABS: Tab[] = [
  { id: "application", label: "My Application" },
  { id: "growth", label: "Organizer Growth" },
  { id: "lookup", label: "Organizer Lookup" },
  { id: "admin", label: "Admin" },
];

export function Dashboard() {
  const [activeTab, setActiveTab] = useState(TABS[0].id);

  return (
    <main className="mx-auto max-w-3xl space-y-6 p-6">
      <h1 className="text-3xl font-bold text-primary">Limitless Organizer Tracker</h1>
      <TabNavigation tabs={TABS} activeTab={activeTab} onTabChange={setActiveTab} />

      {activeTab === "application" && (
        <div className="space-y-8">
          <section>
            <h2 className="mb-2 text-lg font-semibold">Status History</h2>
            <StatusTimeline />
          </section>
          <section>
            <h2 className="mb-2 text-lg font-semibold">Resubmission Log</h2>
            <ResubmissionLog />
          </section>
        </div>
      )}

      {activeTab === "growth" && (
        <div className="space-y-8">
          <section>
            <h2 className="mb-2 text-lg font-semibold">Organizer Activity</h2>
            <OrganizerActivityChart />
          </section>
          <section>
            <h2 className="mb-2 text-lg font-semibold">Wait Time Estimator</h2>
            <WaitTimeEstimator />
          </section>
        </div>
      )}

      {activeTab === "lookup" && (
        <div className="space-y-8">
          <section>
            <h2 className="mb-2 text-lg font-semibold">Highest Organizer ID</h2>
            <HighestOrganizerIdCard />
          </section>
          <section>
            <h2 className="mb-2 text-lg font-semibold">Organizer Profile</h2>
            <OrganizerProfile />
          </section>
        </div>
      )}

      {activeTab === "admin" && (
        <div className="space-y-8">
          <section>
            <h2 className="mb-2 text-lg font-semibold">System Diagnostics</h2>
            <Diagnostics />
          </section>
          <section>
            <h2 className="mb-2 text-lg font-semibold">Task Triggers</h2>
            <TaskTriggers />
          </section>
          <section>
            <h2 className="mb-2 text-lg font-semibold">Configuration</h2>
            <AdminConfig />
          </section>
          <section>
            <h2 className="mb-2 text-lg font-semibold">Event Log</h2>
            <EventLogViewer />
          </section>
        </div>
      )}
    </main>
  );
}
