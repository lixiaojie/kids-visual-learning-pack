export const RESERVED_PAGE_HASHES = ["worlds", "recent-observation"] as const;

function decodeMaybe(value: string) {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export function resolveTopicSlug(search: string, hash: string): string | null {
  const params = new URLSearchParams(search);
  const queryTopic = params.get("topic");
  if (queryTopic) return decodeMaybe(queryTopic);

  const raw = String(hash || "").replace(/^#/, "");
  if (!raw || RESERVED_PAGE_HASHES.includes(raw as (typeof RESERVED_PAGE_HASHES)[number])) {
    return null;
  }

  const topicMatch = raw.match(/^topic\/(.+)$/);
  if (topicMatch?.[1]) return decodeMaybe(topicMatch[1]);

  if (raw.includes("/") || raw.includes("=")) return null;
  return decodeMaybe(raw);
}
