import type { VisualFocus } from "../../../boards/kids-world/src/types/topic";
import type { FocusMode, VisualBinding } from "./interaction-graph";

export function parseFocus(rawFocus?: string | null): Pick<VisualBinding, "focusMode" | "activeRegionIds"> {
  if (!rawFocus || rawFocus === "none:" || rawFocus === "none") {
    return { focusMode: "none", activeRegionIds: [] };
  }

  const [mode, payload = ""] = rawFocus.split(":");
  const ids = payload.split("|").filter(Boolean);

  if (mode === "hotspot") return { focusMode: "hotspot", activeRegionIds: ids.slice(0, 1) };
  if (mode === "path-step") return { focusMode: "path-step", activeRegionIds: ids.slice(0, 1) };
  if (mode === "sequence-progress") return { focusMode: "sequence-progress", activeRegionIds: ids.slice(0, 1) };
  if (mode === "compare-side") return { focusMode: "compare-side", activeRegionIds: ids.slice(0, 1) };
  if (mode === "task-option") return { focusMode: "task-option", activeRegionIds: ids.slice(0, 1) };
  if (mode === "group") return { focusMode: "group", activeRegionIds: ids };
  if (mode === "whole" || mode === "whole-image") return { focusMode: "whole", activeRegionIds: [] };

  return { focusMode: "none", activeRegionIds: [] };
}

export function normalizeFocus(focus?: VisualFocus | null, fallbackId?: string): Pick<VisualBinding, "focusMode" | "activeRegionIds"> {
  if (!focus) {
    return fallbackId ? { focusMode: "task-option", activeRegionIds: [fallbackId] } : { focusMode: "none", activeRegionIds: [] };
  }

  if (focus.mode === "whole-image") return { focusMode: "whole", activeRegionIds: [] };
  return {
    focusMode: focus.mode,
    activeRegionIds: focus.activeRegionIds ?? (fallbackId ? [fallbackId] : []),
  };
}

export function hasVisualFocusDifference(a: VisualBinding | null, b: VisualBinding | null): boolean {
  if (!a || !b) return a !== b;
  return (
    a.assetId !== b.assetId ||
    a.visualSlotId !== b.visualSlotId ||
    a.focusMode !== b.focusMode ||
    a.activeRegionIds.join("|") !== b.activeRegionIds.join("|")
  );
}
