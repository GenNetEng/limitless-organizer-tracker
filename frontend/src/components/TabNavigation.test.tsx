import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TabNavigation, type Tab } from "./TabNavigation";

const tabs: Tab[] = [
  { id: "one", label: "Tab One" },
  { id: "two", label: "Tab Two" },
  { id: "three", label: "Tab Three" },
];

describe("TabNavigation", () => {
  it("renders all tabs with correct labels", () => {
    render(<TabNavigation tabs={tabs} activeTab="one" onTabChange={() => {}} />);

    expect(screen.getByRole("tab", { name: "Tab One" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Tab Two" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Tab Three" })).toBeInTheDocument();
  });

  it("marks the active tab with aria-selected", () => {
    render(<TabNavigation tabs={tabs} activeTab="two" onTabChange={() => {}} />);

    expect(screen.getByRole("tab", { name: "Tab One" })).toHaveAttribute("aria-selected", "false");
    expect(screen.getByRole("tab", { name: "Tab Two" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "Tab Three" })).toHaveAttribute("aria-selected", "false");
  });

  it("calls onTabChange with the tab id when clicked", () => {
    const onChange = vi.fn();
    render(<TabNavigation tabs={tabs} activeTab="one" onTabChange={onChange} />);

    fireEvent.click(screen.getByRole("tab", { name: "Tab Three" }));

    expect(onChange).toHaveBeenCalledWith("three");
  });
});
