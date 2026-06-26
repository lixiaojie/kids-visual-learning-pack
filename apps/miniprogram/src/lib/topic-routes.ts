import type { Locale } from "@yutou/kids-content";

export function hasStaticTopicPage(slug: string): boolean {
  return Boolean(slug);
}

export function getTopicPageUrl(slug: string | undefined, locale: Locale): string {
  return `/pages/topic/index?slug=${slug ?? ""}&locale=${locale}`;
}
