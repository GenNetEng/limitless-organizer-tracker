import type { DateWindow } from "../lib/dateWindow";

const OPTIONS: { value: DateWindow; label: string }[] = [
  { value: "", label: "All time" },
  { value: "30", label: "Last 30 days" },
  { value: "90", label: "Last 90 days" },
  { value: "180", label: "Last 180 days" },
];

interface DateWindowSelectProps {
  id?: string;
  value: DateWindow;
  onChange: (value: DateWindow) => void;
}

export function DateWindowSelect({ id = "date-range-filter", value, onChange }: DateWindowSelectProps) {
  return (
    <div className="form-control w-fit">
      <label htmlFor={id} className="label">
        <span className="label-text">Date Range</span>
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value as DateWindow)}
        className="select select-bordered select-sm"
      >
        {OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
