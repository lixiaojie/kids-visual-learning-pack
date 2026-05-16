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
  VisualFocus,
  VisualFocusMode,
  VisualFocusRegion,
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
  getDefaultEvidenceSourceForStage,
  getTopicLearningFlow,
  getTopicVisualSlots,
  getVisualSlotForTarget,
  getVisualSlotsForRole,
} from "./visual-slots";
export { getTopicEvidenceCoverage, resolveVisualEvidence } from "./evidence";
export { hasVisualFocusDifference, normalizeFocus, parseFocus } from "./focus";
export {
  findNodeBySource,
  getStageById,
  getTopicInteractionGraph,
  taskResultForOption,
} from "./interaction-graph";
export type {
  EvidenceBinding,
  FocusMode,
  MainFlowStage,
  MainFlowStageId,
  SecondaryNode,
  SecondaryNodeKind,
  SubflowContainer,
  SubflowKind,
  TopicInteractionGraph,
  VisualBinding,
} from "./interaction-graph";
export {
  getDefaultActivePath,
  interactionReducer,
  resolveActivePath,
  resolveActivePathBySource,
  resolvePresentation,
} from "./interaction-state";
export type {
  ActiveInteractionPath,
  InteractionAction,
  InteractionPresentation,
} from "./interaction-state";
export { validateInteractionGraph } from "./interaction-validation";
export type { InteractionGraphIssue, InteractionGraphValidationReport } from "./interaction-validation";
export {
  applyTaskOptionClick,
  createInitialTopicInteractionState,
  reduceTopicInteractionState,
  resolveTopicPresentation,
  syncSelectionFromSource,
} from "./interaction";
export type {
  TopicInteractionAction,
  TopicInteractionState,
  TopicPresentation,
} from "./interaction";
