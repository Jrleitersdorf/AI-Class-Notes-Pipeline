export function formatRelativeTime(iso: string | null): string {
  if (!iso) return "never";
  const when = new Date(iso);
  if (Number.isNaN(when.getTime())) return iso;
  const secs = Math.max(0, (Date.now() - when.getTime()) / 1000);
  if (secs < 60) return "just now";
  if (secs < 3600) return `${Math.floor(secs / 60)} min ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)} hr ago`;
  const days = Math.floor(secs / 86400);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}
