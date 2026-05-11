export function getTopicHref(slug: string) {
  return `#topic/${slug}`;
}

export function getExternalHref(href?: string) {
  if (!href) return undefined;
  if (href.startsWith("http") || href.startsWith("../")) return href;
  return `../../${href}`;
}

export function resolveBoardAsset(path?: string) {
  if (!path) return undefined;
  if (/^(https?:|data:|blob:)/.test(path)) return path;

  const normalized = path.replace(/^\/+/, "");
  const baseUrl = ((import.meta as ImportMeta & { env?: { BASE_URL?: string } }).env?.BASE_URL ?? "./");
  const base = baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;

  return `${base}${normalized}`;
}

export function resolveBoardAssetCandidates(path?: string) {
  const primary = resolveBoardAsset(path);
  if (!path || !primary || /^(https?:|data:|blob:)/.test(path)) {
    return primary ? [primary] : [];
  }

  const normalized = path.replace(/^\/+/, "");
  const candidates = [];

  if (typeof window !== "undefined" && window.location.pathname.startsWith("/boards/kids-world/")) {
    candidates.push(`/boards/kids-world/public/${normalized}`);
  }

  candidates.push(primary);

  return [...new Set(candidates)];
}
