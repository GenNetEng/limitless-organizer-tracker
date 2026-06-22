export function formatTimestamp(isoString: string): string {
  return new Date(isoString).toLocaleString();
}

export function formatDateShort(isoDateString: string): string {
  const date = new Date(`${isoDateString}T00:00:00Z`);
  return date.toLocaleDateString(undefined, {
    timeZone: "UTC",
    month: "short",
    day: "numeric",
  });
}

export function formatEpochDate(epochMs: number): string {
  return new Date(epochMs).toLocaleDateString();
}
