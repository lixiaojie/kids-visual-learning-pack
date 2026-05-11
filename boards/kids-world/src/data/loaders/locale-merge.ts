function mergeByIdArray(base: unknown[], overlay: unknown[]): unknown[] {
  const allHaveIds = [...base, ...overlay].every(
    (item) => item && typeof item === "object" && "id" in item,
  );
  if (!allHaveIds) return overlay;

  return base.map((item) => {
    const baseItem = item as { id: string };
    const overlayItem = overlay.find(
      (candidate) => candidate && typeof candidate === "object" && "id" in candidate && candidate.id === baseItem.id,
    );
    return overlayItem ? deepMerge(baseItem, overlayItem) : item;
  });
}

export function deepMerge<T>(base: T, overlay: unknown): T {
  if (Array.isArray(base) && Array.isArray(overlay)) {
    return mergeByIdArray(base, overlay) as T;
  }

  if (
    base &&
    overlay &&
    typeof base === "object" &&
    typeof overlay === "object" &&
    !Array.isArray(base) &&
    !Array.isArray(overlay)
  ) {
    const merged: Record<string, unknown> = { ...(base as Record<string, unknown>) };
    Object.entries(overlay as Record<string, unknown>).forEach(([key, value]) => {
      merged[key] = key in merged ? deepMerge(merged[key], value) : value;
    });
    return merged as T;
  }

  return overlay as T;
}
