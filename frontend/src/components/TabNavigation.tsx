export interface Tab {
  id: string;
  label: string;
}

interface TabNavigationProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

export function TabNavigation({ tabs, activeTab, onTabChange }: TabNavigationProps) {
  return (
    <div role="tablist" className="tabs tabs-bordered">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={activeTab === tab.id ? true : undefined}
          onClick={() => onTabChange(tab.id)}
          className={`tab ${activeTab === tab.id ? "tab-active" : ""}`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
