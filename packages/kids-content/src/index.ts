export type { GeneratedImageAsset } from "../../../boards/kids-world/src/types/assets";
export type { ClickTask, Locale, TaskResult, TextMap, Topic } from "../../../boards/kids-world/src/types/topic";
export type { ExplorationMap, TopicCard, World } from "../../../boards/kids-world/src/types/world";

export { getTopic, hasTopicData } from "../../../boards/kids-world/src/data/loaders/load-topic";
export { deepMerge } from "../../../boards/kids-world/src/data/loaders/locale-merge";
export {
  animationTopicAssetByHref,
  generatedAssets,
  getKnowledgeTopicAssetId,
  getTopicCardAssetId,
  topicHeroAssetBySlug,
} from "../../../boards/kids-world/src/lib/asset-map";

export { getMap, getVisibleTopicSlugs, type ContentChannel } from "./map";
export { getCdnAssetUrl, getGeneratedImageUrl } from "./media";
