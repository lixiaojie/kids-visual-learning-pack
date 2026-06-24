import type { Locale } from "@yutou/kids-content";

const topicPageBySlug: Record<string, string> = {
  "animal-classification-tree": "/packages/topics/animal-classification-tree/index",
  "blood-cells-3d": "/packages/topics/blood-cells-3d/index",
  "cicada-life": "/packages/topics/cicada-life/index",
  digestion: "/packages/topics/digestion/index",
  dinosaurs: "/packages/topics/dinosaurs/index",
  "earth-climate-cities": "/packages/topics/earth-climate-cities/index",
  ecosystem: "/packages/topics/ecosystem/index",
  "insects-and-spiders": "/packages/topics/insects-and-spiders/index",
  "llm-kids-basics": "/packages/topics/llm-kids-basics/index",
  "moon-phases": "/packages/topics/moon-phases/index",
  robots: "/packages/topics/robots/index",
  "solar-system-overview": "/packages/topics/solar-system-overview/index",
  "water-cycle": "/packages/topics/water-cycle/index",
};

export function hasStaticTopicPage(slug: string): boolean {
  return slug in topicPageBySlug;
}

export function getTopicPageUrl(slug: string | undefined, locale: Locale): string {
  const page = slug ? topicPageBySlug[slug] : undefined;
  const target = page ?? `/pages/topic/index?slug=${slug ?? ""}`;
  return target.includes("?") ? `${target}&locale=${locale}` : `${target}?locale=${locale}`;
}
