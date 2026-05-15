export type { GeneratedImageAsset } from "../../../boards/kids-world/src/types/assets";
export type {
  ClickTask,
  EvidenceCoverageReport,
  EvidenceMarkerChip,
  EvidenceResolveContext,
  EvidenceSourcePath,
  EvidenceStatus,
  LearningFlowStage,
  Locale,
  TaskResult,
  TextMap,
  Topic,
  VisualEvidenceBinding,
  VisualEvidenceState,
  VisualSlot,
  VisualSlotRole,
  VisualSlotTarget,
} from "../../../boards/kids-world/src/types/topic";
export type { ExplorationMap, TopicCard, World } from "../../../boards/kids-world/src/types/world";

export { getTopic, hasTopicData } from "./topics";
export {
  generatedAssets,
  getKnowledgeTopicAssetId,
  getTopicCardAssetId,
  topicHeroAssetBySlug,
} from "./assets";

export { getMap, getVisibleTopicSlugs, type ContentChannel } from "./map";
export { getCdnAssetUrl, getGeneratedImageUrl } from "./media";
export {
  getTopicLearningFlow,
  getTopicVisualSlots,
  getVisualSlotForTarget,
  getVisualSlotsForRole,
} from "./visual-slots";
export { getTopicEvidenceCoverage, resolveVisualEvidence } from "./evidence";
