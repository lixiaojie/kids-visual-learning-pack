export function deepMerge<T>(base: T, overlay: Partial<T> | undefined): T {
  if (!overlay) return base;
  if (Array.isArray(base) || Array.isArray(overlay)) {
    if (
      Array.isArray(base) &&
      Array.isArray(overlay) &&
      base.every((item) => item && typeof item === "object" && "id" in item) &&
      overlay.every((item) => item && typeof item === "object" && "id" in item)
    ) {
      const baseById = new Map(base.map((item) => [(item as { id: string }).id, item]));
      return overlay.map((item) => {
        const baseItem = baseById.get((item as { id: string }).id);
        return baseItem ? deepMerge(baseItem, item as Partial<unknown>) : item;
      }) as T;
    }
    return overlay as T;
  }
  if (typeof base !== "object" || typeof overlay !== "object" || base === null || overlay === null) {
    return overlay as T;
  }

  const result: Record<string, unknown> = { ...(base as Record<string, unknown>) };
  for (const [key, value] of Object.entries(overlay)) {
    result[key] = key in result ? deepMerge(result[key], value as Partial<unknown>) : value;
  }
  return result as T;
}
