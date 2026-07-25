import type {
  EvidenceSourcePath,
  EvidenceStatus,
  Locale,
  Topic,
  VisualFocusMode,
  VisualFocusRegion,
  VisualSlot,
} from "../../../boards/kids-world/src/types/topic";
import type { SecondaryNode, SubflowContainer, SubflowKind } from "./interaction-graph";
import { getTopicInteractionGraph } from "./interaction-graph";
import { createInitialTopicInteractionState, type TopicInteractionState } from "./interaction";
import { resolveVisualEvidence } from "./evidence";
import { getTopicLearningFlow } from "./visual-slots";

export type NormalizeTopicInteractionOptions = {
  locale: Locale;
  mode: "dev" | "production";
  platform?: "web" | "miniprogram";
  strictEvidence?: boolean;
};

export type InteractionDiagnostics = {
  errors: string[];
  warnings: string[];
};

export type EvidenceResolution = "explicit" | "derived" | "missing";

export type VisualRegionViewModel = VisualFocusRegion;

export type VisualViewModel = {
  visualSlotId: string;
  assetId: string;
  src: string;
  alt: string;
  aspectRatio?: string;
  activeFocusRegion?: VisualRegionViewModel;
  regions: VisualRegionViewModel[];
  focusMode: VisualFocusMode;
  imageVisibility: "always" | "compact" | "optional";
};

export type NodeViewModel = {
  id: string;
  label: string;
  shortLabel?: string;
  childCopy?: string;
  adultCopy?: string;
  status?: EvidenceStatus;
  sourceKind: string;
  sourceId: string;
  evidence: {
    bindingId?: string;
    visualSlotId?: string;
    focusRegionId?: string;
    resolution: EvidenceResolution;
    focusResolution: EvidenceResolution;
  };
};

export type InteractionBlockKind =
  | "hero"
  | "classification"
  | "objects"
  | "mechanism"
  | "compare"
  | "task"
  | "speak"
  | "parent"
  | "related"
  | "custom";

export type InteractionBlockViewModel = {
  id: string;
  stageId: string;
  subflowId: string;
  kind: InteractionBlockKind;
  title: string;
  description?: string;
  visual: VisualViewModel;
  nodes: NodeViewModel[];
  activeNodeId: string;
  layout: {
    variant: "standard" | "compare" | "task" | "compact";
    desktop: "visual-left" | "visual-top";
    mobile: "visual-first" | "nav-first";
  };
};

export type StageViewModel = {
  id: string;
  order: number;
  label: string;
  shortLabel?: string;
  childPrompt?: string;
  parentPrompt?: string;
  source: "explicit" | "derived";
  quality: "authored" | "fallback";
  blocks: InteractionBlockViewModel[];
};

export type TopicInteractionViewModel = {
  topicId: string;
  locale: Locale;
  stages: StageViewModel[];
  initialState: TopicInteractionState;
  diagnostics: InteractionDiagnostics;
};

function sourceId(source?: string): string {
  if (!source) return "";
  const hashParts = source.split("#");
  if (hashParts[1]) return hashParts[1];
  const parts = source.split(".");
  return parts[parts.length - 1] ?? source;
}

function asEvidenceSource(source?: string): EvidenceSourcePath | null {
  if (!source) return null;
  const baseSource = source.split("#")[0];
  if (
    baseSource.startsWith("classificationGroups.") ||
    baseSource.startsWith("representativeObjects.") ||
    baseSource.startsWith("mechanism.steps.") ||
    baseSource.startsWith("secondaryMechanism.steps.") ||
    baseSource.startsWith("comparePairs.") ||
    baseSource.startsWith("clickTasks.")
  ) {
    return baseSource as EvidenceSourcePath;
  }
  return null;
}

function blockKind(kind: SubflowKind): InteractionBlockKind {
  if (kind === "classificationGroup") return "classification";
  if (kind === "objectGroup" || kind === "objectDetail") return "objects";
  if (kind === "mechanism" || kind === "secondaryMechanism") return "mechanism";
  if (kind === "comparePair") return "compare";
  if (kind === "clickTask") return "task";
  if (kind === "summary") return "speak";
  if (kind === "parentGuide") return "parent";
  if (kind === "relatedTopics") return "related";
  if (kind === "hero") return "hero";
  return "custom";
}

function layoutVariant(kind: InteractionBlockKind): InteractionBlockViewModel["layout"]["variant"] {
  if (kind === "compare") return "compare";
  if (kind === "task") return "task";
  if (kind === "hero" || kind === "speak" || kind === "parent" || kind === "related") return "compact";
  return "standard";
}

function findSlot(topic: Topic, visualSlotId?: string | null): VisualSlot | null {
  return visualSlotId ? topic.visualSlots?.find((slot) => slot.id === visualSlotId) ?? null : null;
}

function bindingForSource(topic: Topic, source?: string | null) {
  const evidenceSource = asEvidenceSource(source ?? undefined);
  if (!evidenceSource) return null;
  return topic.visualEvidenceBindings?.find((binding) => binding.source === evidenceSource) ?? null;
}

function nodeEvidence(topic: Topic, source?: string | null) {
  const evidenceSource = asEvidenceSource(source ?? undefined);
  if (!evidenceSource) return { evidence: null, binding: null, resolution: "missing" as EvidenceResolution };
  const evidence = resolveVisualEvidence(topic, { source: evidenceSource });
  const binding = bindingForSource(topic, evidenceSource);
  return {
    evidence,
    binding,
    resolution: evidence?.bindingQuality ?? "missing" as EvidenceResolution,
  };
}

function visualFrom(topic: Topic, source: string | undefined, fallbackVisualSlotId: string | undefined): VisualViewModel {
  const { evidence } = nodeEvidence(topic, source);
  const slot = findSlot(topic, evidence?.visualSlotId) ?? findSlot(topic, fallbackVisualSlotId);
  const activeRegionId = evidence?.focus?.activeRegionIds?.[0];
  const regions = evidence?.focus?.regions ?? [];
  const activeFocusRegion = activeRegionId ? regions.find((region) => region.id === activeRegionId) : undefined;

  return {
    visualSlotId: slot?.id ?? evidence?.visualSlotId ?? fallbackVisualSlotId ?? "",
    assetId: slot?.assetId ?? "",
    src: slot?.assetId ?? "",
    alt: slot?.alt ?? slot?.caption ?? "",
    activeFocusRegion,
    regions,
    focusMode: evidence?.focus?.mode ?? "none",
    imageVisibility: "always",
  };
}

function normalizeNode(topic: Topic, node: SecondaryNode): NodeViewModel {
  const { evidence, binding, resolution } = nodeEvidence(topic, node.source);
  const activeRegionId = evidence?.focus?.activeRegionIds?.[0];
  const focusResolution = binding?.focus?.activeRegionIds?.length || binding?.focus?.regions?.length
    ? "explicit"
    : activeRegionId
      ? "derived"
      : "missing";
  return {
    id: node.id,
    label: node.label,
    childCopy: evidence?.evidenceCopy ?? node.evidence?.copy,
    adultCopy: node.evidence?.hint,
    status: evidence?.status,
    sourceKind: node.kind,
    sourceId: sourceId(node.source),
    evidence: {
      bindingId: binding?.id,
      visualSlotId: evidence?.visualSlotId ?? node.visual?.visualSlotId,
      focusRegionId: activeRegionId,
      resolution,
      focusResolution,
    },
  };
}

function sourceForSubflowDefault(subflow: SubflowContainer): string | undefined {
  if (subflow.defaultNodeId) {
    return subflow.nodes.find((node) => node.id === subflow.defaultNodeId)?.source ?? subflow.source;
  }
  return subflow.nodes[0]?.source ?? subflow.source;
}

function normalizeBlock(
  topic: Topic,
  stageId: string,
  graphStageId: string,
  subflow: SubflowContainer,
): InteractionBlockViewModel {
  const kind = blockKind(subflow.kind);
  const nodes = subflow.nodes.map((node) => normalizeNode(topic, node));
  const activeNodeId = subflow.defaultNodeId ?? nodes[0]?.id ?? subflow.id;
  const activeSource = sourceForSubflowDefault(subflow);

  return {
    id: graphStageId === stageId
      ? `${stageId}-${subflow.id}`
      : `${stageId}-${graphStageId}-${subflow.id}`,
    stageId,
    subflowId: subflow.id,
    kind,
    title: subflow.label,
    visual: visualFrom(topic, activeSource, subflow.visual?.visualSlotId),
    nodes,
    activeNodeId,
    layout: {
      variant: layoutVariant(kind),
      desktop: kind === "hero" ? "visual-top" : "visual-left",
      mobile: "visual-first",
    },
  };
}

function collectDiagnostics(blocks: InteractionBlockViewModel[], options: NormalizeTopicInteractionOptions): InteractionDiagnostics {
  const diagnostics: InteractionDiagnostics = { errors: [], warnings: [] };
  for (const block of blocks) {
    for (const node of block.nodes) {
      if (node.evidence.resolution === "explicit") continue;
      const message = `${block.stageId}/${block.subflowId}/${node.id} evidence resolved as ${node.evidence.resolution}`;
      if (options.strictEvidence) diagnostics.errors.push(message);
      else diagnostics.warnings.push(message);
    }
  }
  for (const block of blocks) {
    for (const node of block.nodes) {
      if (!node.evidence.visualSlotId) {
        diagnostics.errors.push(`${block.stageId}/${block.subflowId}/${node.id} missing visual slot`);
      }
      if (node.evidence.focusResolution === "explicit") continue;
      const message = `${block.stageId}/${block.subflowId}/${node.id} missing focus region (${node.evidence.focusResolution})`;
      if (options.strictEvidence) diagnostics.errors.push(message);
      else diagnostics.warnings.push(message);
    }
  }
  return diagnostics;
}

export function normalizeTopicInteraction(topic: Topic, options: NormalizeTopicInteractionOptions): TopicInteractionViewModel {
  const flowStages = getTopicLearningFlow(topic, options.locale);
  const graph = getTopicInteractionGraph(topic, options.locale);
  const flowWasAuthored = Boolean(topic.learningFlow?.length);
  const graphStageIds = new Set<string>(graph.stages.map((stage) => stage.id));
  if (flowWasAuthored) {
    const seenStageIds = new Set<string>();
    for (const flowStage of flowStages) {
      if (!graphStageIds.has(flowStage.id)) {
        throw new Error(`unknown authored learning flow stage: ${flowStage.id}`);
      }
      if (seenStageIds.has(flowStage.id)) {
        throw new Error(`duplicate authored learning flow stage: ${flowStage.id}`);
      }
      seenStageIds.add(flowStage.id);
    }
  }
  const authoredStageIds = new Set(flowStages.map((stage) => stage.id));

  const stages: StageViewModel[] = flowStages.map((flowStage, index) => {
    const graphStageIndex = graph.stages.findIndex((stage) => stage.id === flowStage.id);
    const followingAuthoredStageIndex = graph.stages.findIndex(
      (stage, candidateIndex) => candidateIndex > graphStageIndex && authoredStageIds.has(stage.id),
    );
    const nextGraphStageIndex =
      followingAuthoredStageIndex >= 0 ? followingAuthoredStageIndex : graph.stages.length;
    const graphStages = graphStageIndex >= 0
      ? graph.stages.slice(graphStageIndex, nextGraphStageIndex)
      : [];
    const blocks = graphStages.flatMap((graphStage) =>
      graphStage.subflows.map((subflow) =>
        normalizeBlock(topic, flowStage.id, graphStage.id, subflow)
      )
    );
    return {
      id: flowStage.id,
      order: index + 1,
      label: flowStage.label,
      childPrompt: flowStage.childPrompt,
      source: flowWasAuthored ? "explicit" : "derived",
      quality: flowWasAuthored ? "authored" : "fallback",
      blocks,
    };
  });

  const allBlocks = stages.flatMap((stage) => stage.blocks);
  return {
    topicId: topic.slug,
    locale: options.locale,
    stages,
    initialState: createInitialTopicInteractionState(topic, options.locale),
    diagnostics: collectDiagnostics(allBlocks, options),
  };
}
