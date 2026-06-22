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
    <div role="tablist" className="flex gap-1 rounded-lg bg-base-200 p-1">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={activeTab === tab.id ? true : undefined}
          onClick={() => onTabChange(tab.id)}
          className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === tab.id
              ? "bg-primary text-primary-content shadow-sm"
              : "text-base-content/70 hover:text-base-content"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
