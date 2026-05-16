import type { EvidenceStatus } from "../../../boards/kids-world/src/types/topic";
import type {
  EvidenceBinding,
  FocusMode,
  MainFlowStage,
  MainFlowStageId,
  SecondaryNode,
  SubflowContainer,
  TopicInteractionGraph,
  VisualBinding,
} from "./interaction-graph";
import { findNodeBySource, getStageById } from "./interaction-graph";

export type ActiveInteractionPath = {
  stageId: MainFlowStageId;
  subflowId: string | null;
  nodeId: string | null;
  source: string | null;
  visualSlotId: string | null;
  assetId: string | null;
  focusMode: FocusMode | null;
  activeRegionIds: string[];
  evidenceTitle?: string;
  evidenceCopy?: string;
  status?: EvidenceStatus;
};

export type InteractionAction =
  | { type: "selectStage"; stageId: MainFlowStageId }
  | { type: "selectSubflow"; stageId?: MainFlowStageId; subflowId: string }
  | { type: "selectNode"; stageId?: MainFlowStageId; subflowId?: string; nodeId: string }
  | { type: "selectSource"; source: string }
  | { type: "resetTopic"; slug: string }
  | { type: "markTaskResult"; taskId: string; optionId: string; status: EvidenceStatus };

export type InteractionPresentation = {
  stage: MainFlowStage;
  subflow: SubflowContainer | null;
  node: SecondaryNode | null;
  visual: VisualBinding | null;
  evidence: EvidenceBinding | null;
};

function emptyPath(graph: TopicInteractionGraph): ActiveInteractionPath {
  const firstStage = graph.stages[0];
  return {
    stageId: firstStage?.id ?? "observe",
    subflowId: null,
    nodeId: null,
    source: null,
    visualSlotId: null,
    assetId: null,
    focusMode: null,
    activeRegionIds: [],
    status: "idle",
  };
}

function findSubflow(stage: MainFlowStage | null, subflowId?: string | null): SubflowContainer | null {
  if (!stage) return null;
  return stage.subflows.find((subflow) => subflow.id === subflowId) ?? stage.subflows[0] ?? null;
}

function findNode(subflow: SubflowContainer | null, nodeId?: string | null): SecondaryNode | null {
  if (!subflow || !nodeId) return null;
  return subflow.nodes.find((node) => node.id === nodeId) ?? null;
}

function defaultNodeForSubflow(subflow: SubflowContainer | null): SecondaryNode | null {
  if (!subflow || subflow.kind === "clickTask") return null;
  return findNode(subflow, subflow.defaultNodeId) ?? null;
}

function pathFromParts(
  graph: TopicInteractionGraph,
  stageItem: MainFlowStage | null,
  subflow: SubflowContainer | null,
  node: SecondaryNode | null,
  status: EvidenceStatus = "selected",
): ActiveInteractionPath {
  if (!stageItem) return emptyPath(graph);
  const visual = node?.visual ?? subflow?.visual ?? null;
  const evidence = node?.evidence ?? null;
  return {
    stageId: stageItem.id,
    subflowId: subflow?.id ?? null,
    nodeId: node?.id ?? null,
    source: node?.source ?? subflow?.source ?? stageItem.defaultSource,
    visualSlotId: visual?.visualSlotId ?? null,
    assetId: visual?.assetId ?? null,
    focusMode: visual?.focusMode ?? null,
    activeRegionIds: visual?.activeRegionIds ?? [],
    evidenceTitle: evidence?.title,
    evidenceCopy: evidence?.copy,
    status,
  };
}

export function getDefaultActivePath(graph: TopicInteractionGraph, stageId?: MainFlowStageId): ActiveInteractionPath {
  const stageItem = (stageId ? getStageById(graph, stageId) : graph.stages[0]) ?? graph.stages[0] ?? null;
  if (!stageItem) return emptyPath(graph);
  const subflow = findSubflow(stageItem, stageItem.defaultSubflowId);
  const node = defaultNodeForSubflow(subflow);
  return pathFromParts(graph, stageItem, subflow, node, "idle");
}

export function resolveActivePath(
  graph: TopicInteractionGraph,
  input: {
    stageId: MainFlowStageId;
    subflowId?: string | null;
    nodeId?: string | null;
    status?: EvidenceStatus;
  },
): ActiveInteractionPath {
  const stageItem = getStageById(graph, input.stageId) ?? graph.stages[0] ?? null;
  const subflow = findSubflow(stageItem, input.subflowId ?? stageItem?.defaultSubflowId);
  const explicitNode = findNode(subflow, input.nodeId);
  const node = input.nodeId ? explicitNode : defaultNodeForSubflow(subflow);
  return pathFromParts(graph, stageItem, subflow, node, input.status ?? "selected");
}

export function resolveActivePathBySource(graph: TopicInteractionGraph, source: string): ActiveInteractionPath {
  const match = findNodeBySource(graph, source);
  if (!match) return getDefaultActivePath(graph);
  return pathFromParts(graph, match.stage, match.subflow, match.node, "selected");
}

export function resolvePresentation(graph: TopicInteractionGraph, activePath: ActiveInteractionPath): InteractionPresentation {
  const stageItem = getStageById(graph, activePath.stageId) ?? graph.stages[0];
  const subflow = findSubflow(stageItem, activePath.subflowId);
  const node = findNode(subflow, activePath.nodeId);
  return {
    stage: stageItem,
    subflow,
    node,
    visual: node?.visual ?? subflow?.visual ?? null,
    evidence: node?.evidence ?? null,
  };
}

export function interactionReducer(
  graph: TopicInteractionGraph,
  current: ActiveInteractionPath,
  action: InteractionAction,
): ActiveInteractionPath {
  if (action.type === "selectStage") {
    return getDefaultActivePath(graph, action.stageId);
  }

  if (action.type === "selectSubflow") {
    return resolveActivePath(graph, {
      stageId: action.stageId ?? current.stageId,
      subflowId: action.subflowId,
    });
  }

  if (action.type === "selectNode") {
    return resolveActivePath(graph, {
      stageId: action.stageId ?? current.stageId,
      subflowId: action.subflowId ?? current.subflowId,
      nodeId: action.nodeId,
    });
  }

  if (action.type === "selectSource") {
    return resolveActivePathBySource(graph, action.source);
  }

  if (action.type === "resetTopic") {
    return getDefaultActivePath(graph);
  }

  if (action.type === "markTaskResult") {
    return resolveActivePath(graph, {
      stageId: "tasks",
      subflowId: action.taskId,
      nodeId: action.optionId,
      status: action.status,
    });
  }

  return current;
}
