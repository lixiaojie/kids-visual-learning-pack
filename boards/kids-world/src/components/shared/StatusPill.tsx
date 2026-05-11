import type { ExplorationMap } from "../../types/world";

export function StatusPill({ status, map }: { status: string; map: ExplorationMap }) {
  const statusText = map.statusLegend.find((item) => item.status === status);
  return <span className={`status-pill status-${status}`}>{statusText?.childLabel ?? status}</span>;
}
