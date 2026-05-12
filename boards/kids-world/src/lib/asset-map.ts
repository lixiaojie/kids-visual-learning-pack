import imageManifest from "../data/image-generation-manifest.json";
import type { GeneratedImageAsset } from "../types/assets";
import type { TopicCard } from "../types/world";

export const generatedAssets = (imageManifest.assets as GeneratedImageAsset[]).reduce<Record<string, GeneratedImageAsset>>((acc, asset) => {
  acc[asset.assetId] = asset;
  return acc;
}, {});

export const topicHeroAssetBySlug: Record<string, string> = {
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

export const animationTopicAssetByHref: Array<[string, string]> = [
  ["spider-verse", "animation-spider-verse-card"],
  ["paw-patrol", "animation-paw-patrol-card"],
];

export function getTopicCardAssetId(topic: TopicCard) {
  return animationTopicAssetByHref.find(([hrefFragment]) => topic.href?.includes(hrefFragment))?.[1];
}

export function getKnowledgeTopicAssetId(topic: TopicCard) {
  return topic.slug ? topicHeroAssetBySlug[topic.slug] : undefined;
}
