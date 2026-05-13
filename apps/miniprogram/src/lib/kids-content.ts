import explorationMapBase from "../../../../boards/kids-world/src/data/exploration-map.json";
import explorationMapEn from "../../../../boards/kids-world/src/data/locales/en-US/exploration-map.json";
import imageManifest from "../../../../boards/kids-world/src/data/image-generation-manifest.json";
import channelPolicy from "../../../../channel-policy.json";

import animalTreeBase from "../../../../boards/kids-world/src/data/topics/animal-classification-tree.json";
import animalTreeEn from "../../../../boards/kids-world/src/data/locales/en-US/topics/animal-classification-tree.json";
import bloodCellsBase from "../../../../boards/kids-world/src/data/topics/blood-cells-3d.json";
import bloodCellsEn from "../../../../boards/kids-world/src/data/locales/en-US/topics/blood-cells-3d.json";
import climateBase from "../../../../boards/kids-world/src/data/topics/earth-climate-cities.json";
import climateEn from "../../../../boards/kids-world/src/data/locales/en-US/topics/earth-climate-cities.json";
import digestionBase from "../../../../boards/kids-world/src/data/topics/digestion.json";
import digestionEn from "../../../../boards/kids-world/src/data/locales/en-US/topics/digestion.json";
import dinosaursBase from "../../../../boards/kids-world/src/data/topics/dinosaurs.json";
import dinosaursEn from "../../../../boards/kids-world/src/data/locales/en-US/topics/dinosaurs.json";
import ecosystemBase from "../../../../boards/kids-world/src/data/topics/ecosystem.json";
import ecosystemEn from "../../../../boards/kids-world/src/data/locales/en-US/topics/ecosystem.json";
import insectsBase from "../../../../boards/kids-world/src/data/topics/insects-and-spiders.json";
import insectsEn from "../../../../boards/kids-world/src/data/locales/en-US/topics/insects-and-spiders.json";
import llmBase from "../../../../boards/kids-world/src/data/topics/llm-kids-basics.json";
import llmEn from "../../../../boards/kids-world/src/data/locales/en-US/topics/llm-kids-basics.json";
import moonPhasesBase from "../../../../boards/kids-world/src/data/topics/moon-phases.json";
import moonPhasesEn from "../../../../boards/kids-world/src/data/locales/en-US/topics/moon-phases.json";
import robotsBase from "../../../../boards/kids-world/src/data/topics/robots.json";
import robotsEn from "../../../../boards/kids-world/src/data/locales/en-US/topics/robots.json";
import solarBase from "../../../../boards/kids-world/src/data/topics/solar-system-overview.json";
import solarEn from "../../../../boards/kids-world/src/data/locales/en-US/topics/solar-system-overview.json";
import waterCycleBase from "../../../../boards/kids-world/src/data/topics/water-cycle.json";
import waterCycleEn from "../../../../boards/kids-world/src/data/locales/en-US/topics/water-cycle.json";

export type Locale = "zh-CN" | "en-US";
export type TaskResult = "idle" | "correct" | "wrong";
export type ClickTask = {
  id: string;
  type: "singleChoice" | "findTarget" | "sequenceClick" | string;
  title: string;
  prompt?: string;
  options?: Array<{ id: string; label: string }>;
  correctOptionId?: string;
  correctSequence?: string[];
  targetIds?: string[];
  decoyIds?: string[];
  wrongHint?: string;
  wrongHints?: Record<string, string>;
  successCopy?: string;
};
export type Topic = any;
export type ContentChannel = keyof typeof channelPolicy;

const defaultCdnBase = "https://kids.yutou-verse.cn/boards/kids-world";

const topicBaseBySlug: Record<string, Topic> = {
  "animal-classification-tree": animalTreeBase,
  "blood-cells-3d": bloodCellsBase,
  digestion: digestionBase,
  dinosaurs: dinosaursBase,
  "earth-climate-cities": climateBase,
  ecosystem: ecosystemBase,
  "insects-and-spiders": insectsBase,
  "llm-kids-basics": llmBase,
  "moon-phases": moonPhasesBase,
  robots: robotsBase,
  "solar-system-overview": solarBase,
  "water-cycle": waterCycleBase,
};

const topicEnBySlug: Record<string, Partial<Topic>> = {
  "animal-classification-tree": animalTreeEn,
  "blood-cells-3d": bloodCellsEn,
  digestion: digestionEn,
  dinosaurs: dinosaursEn,
  "earth-climate-cities": climateEn,
  ecosystem: ecosystemEn,
  "insects-and-spiders": insectsEn,
  "llm-kids-basics": llmEn,
  "moon-phases": moonPhasesEn,
  robots: robotsEn,
  "solar-system-overview": solarEn,
  "water-cycle": waterCycleEn,
};

const topicHeroAssetBySlug: Record<string, string> = {
  "animal-classification-tree": "life-animal-classification-tree-hero",
  "blood-cells-3d": "body-blood-cells-3d-hero",
  digestion: "body-digestion-hero",
  dinosaurs: "life-dinosaurs-hero",
  "earth-climate-cities": "earth-climate-cities-hero",
  ecosystem: "life-ecosystem-hero",
  "insects-and-spiders": "life-insects-and-spiders-hero",
  "llm-kids-basics": "human-made-llm-kids-basics-hero",
  "moon-phases": "space-moon-phases-hero",
  robots: "human-system-robots-hero",
  "solar-system-overview": "space-solar-system-overview-hero",
  "water-cycle": "earth-water-cycle-hero",
};

const generatedAssets = (imageManifest.assets as Array<{ assetId: string; webpPath?: string }>).reduce<
  Record<string, { assetId: string; webpPath?: string }>
>((acc, asset) => {
  acc[asset.assetId] = asset;
  return acc;
}, {});

function deepMerge<T>(base: T, overlay: Partial<T> | undefined): T {
  if (!overlay) return base;
  if (Array.isArray(base) || Array.isArray(overlay)) return overlay as T;
  if (typeof base !== "object" || typeof overlay !== "object" || base === null || overlay === null) {
    return overlay as T;
  }

  const result: Record<string, unknown> = { ...(base as Record<string, unknown>) };
  for (const [key, value] of Object.entries(overlay)) {
    result[key] = key in result ? deepMerge(result[key], value as Partial<unknown>) : value;
  }
  return result as T;
}

function normalizeBase(base: string) {
  return base.replace(/\/+$/, "");
}

export function getTopic(slug: string, locale: Locale): Topic | null {
  const base = topicBaseBySlug[slug];
  if (!base) return null;
  return locale === "en-US" ? deepMerge(base, topicEnBySlug[slug]) : base;
}

export function getMap(locale: Locale, channel: ContentChannel = "miniprogram") {
  const localizedMap = locale === "en-US" ? deepMerge(explorationMapBase, explorationMapEn) : explorationMapBase;
  const policy = channelPolicy[channel];
  const visibleTopics = policy.visibleTopics;
  const worlds = localizedMap.worlds
    .map((world) => ({
      ...world,
      topicCards: world.topicCards.filter((topic) => {
        if (!topic.slug) return false;
        if (visibleTopics === "all") return true;
        if (visibleTopics === "all-render-ready") return topic.slug in topicBaseBySlug;
        return visibleTopics.includes(topic.slug);
      }),
    }))
    .filter((world) => world.topicCards.length > 0);
  return { ...localizedMap, worlds };
}

export function getVisibleTopicSlugs(channel: ContentChannel = "miniprogram"): string[] {
  const visibleTopics = channelPolicy[channel].visibleTopics;
  if (visibleTopics === "all") return Object.keys(topicBaseBySlug);
  if (visibleTopics === "all-render-ready") return Object.keys(topicBaseBySlug);
  return [...visibleTopics];
}

export function getKnowledgeTopicAssetId(topic: { slug?: string }) {
  return topic.slug ? topicHeroAssetBySlug[topic.slug] : undefined;
}

export function getCdnAssetUrl(assetPath: string | undefined, cdnBase = defaultCdnBase): string | undefined {
  if (!assetPath) return undefined;
  const normalizedPath = assetPath.startsWith("/") ? assetPath : `/${assetPath}`;
  return `${normalizeBase(cdnBase)}${normalizedPath}`;
}

export function getGeneratedImageUrl(assetId: string | undefined, cdnBase = defaultCdnBase): string | undefined {
  if (!assetId) return undefined;
  return getCdnAssetUrl(generatedAssets[assetId]?.webpPath, cdnBase);
}
