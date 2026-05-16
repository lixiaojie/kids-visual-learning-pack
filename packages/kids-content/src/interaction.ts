import type {
  ClickTask,
  EvidenceSourcePath,
  EvidenceStatus,
  Locale,
  Topic,
  VisualEvidenceState,
  VisualSlot,
} from "../../../boards/kids-world/src/types/topic";
import { resolveVisualEvidence } from "./evidence";
import { getTopicInteractionGraph } from "./interaction-graph";
import {
  getDefaultActivePath,
  interactionReducer as reduceInteractionPath,
  resolveActivePath,
  resolveActivePathBySource,
  resolvePresentation as resolveGraphPresentation,
  type ActiveInteractionPath,
} from "./interaction-state";

export type TopicInteractionState = {
  activeStageId: string;
  activePath?: ActiveInteractionPath;
  activeEvidenceSource?: EvidenceSourcePath;
  activeVisualSlotId?: string;
  activeGroupId?: string;
  activeObjectId?: string;
  activeMechanismStepId?: string;
  activeSecondaryStepId?: string;
  activeComparePairId?: string;
  activeTaskId?: string;
  taskSelectedIds: Record<string, string[]>;
  taskResults: Record<string, EvidenceStatus>;
  taskMessages: Record<string, string>;
  lastIntent?: "init" | "flow" | "control" | "task" | "scroll";
  lockedUntil?: number;
};

export type TopicPresentation = {
  state: TopicInteractionState;
  visualSlot?: VisualSlot | null;
  evidence?: VisualEvidenceState | null;
  activeStageId: string;
};

export type TopicInteractionAction =
  | { type: "RESET_TOPIC"; topic: Topic; locale: Locale }
  | { type: "SELECT_STAGE"; stageId: string; now?: number }
  | { type: "SCROLL_STAGE_VISIBLE"; stageId: string; now?: number }
  | { type: "SELECT_EVIDENCE_SOURCE"; source: EvidenceSourcePath; now?: number }
  | { type: "SELECT_CLASSIFICATION_GROUP"; groupId: string; now?: number }
  | { type: "SELECT_REPRESENTATIVE_OBJECT"; objectId: string; now?: number }
  | { type: "SELECT_MECHANISM_STEP"; stepId: string; now?: number }
  | { type: "SELECT_SECONDARY_MECHANISM_STEP"; stepId: string; now?: number }
  | { type: "SELECT_COMPARE_PAIR"; pairId: string; now?: number }
  | { type: "SELECT_COMPARE_SIDE"; pairId: string; side: "a" | "b"; now?: number }
  | { type: "SELECT_CLICK_TASK"; taskId: string; now?: number }
  | { type: "CLICK_TASK_OPTION"; taskId: string; optionId: string; now?: number };

const interactionLockMs = 800;

function parts(source: EvidenceSourcePath) {
  return source.split(".");
}

function stageIdForSource(source?: EvidenceSourcePath): string | undefined {
  if (!source) return undefined;
  if (source.startsWith("classificationGroups.")) return "classify";
  if (source.startsWith("representativeObjects.")) return "inspect";
  if (source.startsWith("mechanism.steps.") || source.startsWith("secondaryMechanism.steps.")) return "trace";
  if (source.startsWith("comparePairs.")) return "compare";
  if (source.startsWith("clickTasks.")) return "tasks";
  return undefined;
}

function asEvidenceSource(source?: string | null): EvidenceSourcePath | undefined {
  if (!source) return undefined;
  if (
    source.startsWith("classificationGroups.") ||
    source.startsWith("representativeObjects.") ||
    source.startsWith("mechanism.steps.") ||
    source.startsWith("secondaryMechanism.steps.") ||
    source.startsWith("comparePairs.") ||
    source.startsWith("clickTasks.")
  ) {
    return source as EvidenceSourcePath;
  }
  return undefined;
}

function syncSelectionFromPath(topic: Topic, state: TopicInteractionState, activePath: ActiveInteractionPath): TopicInteractionState {
  const source = activePath.source ?? undefined;
  const sourceParts = source?.split(".") ?? [];
  const activeStageId = activePath.stageId;
  const activeEvidenceSource = asEvidenceSource(source);
  let next: TopicInteractionState = {
    ...state,
    activePath,
    activeStageId,
    activeEvidenceSource,
  };

  if (!source) return next;

  if (source.startsWith("classificationGroups.")) {
    const groupId = sourceParts[1];
    return {
      ...next,
      activeGroupId: groupId,
      activeObjectId: activePath.nodeId ?? topic.representativeObjects.find((item) => item.groupId === groupId)?.id ?? next.activeObjectId,
    };
  }

  if (source.startsWith("representativeObjects.")) {
    const objectId = sourceParts[1];
    const object = topic.representativeObjects.find((item) => item.id === objectId);
    return {
      ...next,
      activeObjectId: objectId,
      activeGroupId: object?.groupId ?? next.activeGroupId,
    };
  }

  if (source.startsWith("mechanism.steps.")) {
    return { ...next, activeMechanismStepId: sourceParts[2] };
  }

  if (source.startsWith("secondaryMechanism.steps.")) {
    return { ...next, activeSecondaryStepId: sourceParts[2] };
  }

  if (source.startsWith("comparePairs.")) {
    const pairId = source.slice("comparePairs.".length).split("#")[0];
    return { ...next, activeComparePairId: pairId };
  }

  if (source.startsWith("clickTasks.")) {
    return { ...next, activeTaskId: sourceParts[1] };
  }

  return next;
}

export function getTaskOptions(task: ClickTask): Array<{ id: string; label: string }> {
  return (
    task.options ??
    [...(task.targetIds ?? []), ...(task.decoyIds ?? [])].map((id) => ({
      id,
      label: id.replace(/-/g, " "),
    }))
  );
}

function getWrongHint(task: ClickTask, optionId: string, locale: Locale): string {
  if (task.wrongHints?.[optionId]) return task.wrongHints[optionId];
  return task.wrongHint ?? (locale === "en-US" ? "Look for one more clue and try again." : "再观察一个线索试试看。");
}

export function syncSelectionFromSource(topic: Topic, state: TopicInteractionState): TopicInteractionState {
  const source = state.activeEvidenceSource;
  if (!source) return state;

  const sourceParts = parts(source);
  const activeStageId = stageIdForSource(source) ?? state.activeStageId;

  if (source.startsWith("classificationGroups.")) {
    const groupId = sourceParts[1];
    const firstObject = topic.representativeObjects.find((item) => item.groupId === groupId);
    return {
      ...state,
      activeStageId,
      activeGroupId: groupId,
      activeObjectId: firstObject?.id ?? state.activeObjectId,
    };
  }

  if (source.startsWith("representativeObjects.")) {
    const objectId = sourceParts[1];
    const object = topic.representativeObjects.find((item) => item.id === objectId);
    return {
      ...state,
      activeStageId,
      activeObjectId: objectId,
      activeGroupId: object?.groupId ?? state.activeGroupId,
    };
  }

  if (source.startsWith("mechanism.steps.")) {
    return { ...state, activeStageId, activeMechanismStepId: sourceParts[2] };
  }

  if (source.startsWith("secondaryMechanism.steps.")) {
    return { ...state, activeStageId, activeSecondaryStepId: sourceParts[2] };
  }

  if (source.startsWith("comparePairs.")) {
    return { ...state, activeStageId, activeComparePairId: sourceParts[1] };
  }

  if (source.startsWith("clickTasks.")) {
    return { ...state, activeStageId, activeTaskId: sourceParts[1] };
  }

  return state;
}

export function createInitialTopicInteractionState(topic: Topic, locale: Locale): TopicInteractionState {
  const graph = getTopicInteractionGraph(topic, locale);
  const activePath = getDefaultActivePath(graph);
  return syncSelectionFromPath(topic, {
    activeStageId: activePath.stageId,
    activePath,
    taskSelectedIds: {},
    taskResults: {},
    taskMessages: {},
    lastIntent: "init",
  }, activePath);
}

export function applyTaskOptionClick(
  topic: Topic,
  state: TopicInteractionState,
  locale: Locale,
  taskId: string,
  optionId: string,
  now = Date.now(),
): TopicInteractionState {
  const task = topic.clickTasks.find((item) => item.id === taskId);
  if (!task) return state;

  const prevSelected = state.taskSelectedIds[taskId] ?? [];
  let nextSelected: string[] = prevSelected;
  let nextResult: EvidenceStatus = "selected";
  let message = "";

  if (task.type === "singleChoice") {
    nextSelected = [optionId];
    if (optionId === task.correctOptionId) {
      nextResult = "correct";
      message = task.successCopy ?? "";
    } else {
      nextResult = "wrong";
      message = getWrongHint(task, optionId, locale);
    }
  } else if (task.type === "findTarget") {
    if (task.targetIds?.includes(optionId)) {
      nextSelected = Array.from(new Set([...prevSelected, optionId]));
      const complete = task.targetIds.every((id) => nextSelected.includes(id));
      nextResult = complete ? "complete" : "partial";
      message = complete ? task.successCopy ?? "" : task.prompt ?? task.title;
    } else {
      nextSelected = [optionId];
      nextResult = "wrong";
      message = getWrongHint(task, optionId, locale);
    }
  } else if (task.type === "sequenceClick") {
    const expected = task.correctSequence?.[prevSelected.length];
    if (optionId !== expected) {
      nextSelected = [];
      nextResult = "wrong";
      message = getWrongHint(task, optionId, locale);
    } else {
      nextSelected = [...prevSelected, optionId];
      const complete = nextSelected.length === task.correctSequence?.length;
      nextResult = complete ? "complete" : "partial";
      message = complete ? task.successCopy ?? "" : task.prompt ?? task.title;
    }
  }

  const graph = getTopicInteractionGraph(topic, locale);
  const activePath = reduceInteractionPath(
    graph,
    state.activePath ?? getDefaultActivePath(graph, "tasks"),
    { type: "markTaskResult", taskId, optionId, status: nextResult },
  );

  return syncSelectionFromPath(topic, {
    ...state,
    activeTaskId: taskId,
    taskSelectedIds: { ...state.taskSelectedIds, [taskId]: nextSelected },
    taskResults: { ...state.taskResults, [taskId]: nextResult },
    taskMessages: { ...state.taskMessages, [taskId]: message },
    lastIntent: "task",
    lockedUntil: now + interactionLockMs,
  }, activePath);
}

export function reduceTopicInteractionState(
  topic: Topic,
  locale: Locale,
  state: TopicInteractionState,
  action: TopicInteractionAction,
): TopicInteractionState {
  const now = "now" in action && action.now ? action.now : Date.now();
  const graph = getTopicInteractionGraph(topic, locale);
  const currentPath = state.activePath ?? getDefaultActivePath(graph);

  if (action.type === "RESET_TOPIC") {
    return createInitialTopicInteractionState(action.topic, action.locale);
  }

  if (action.type === "SCROLL_STAGE_VISIBLE") {
    if (state.lockedUntil && now < state.lockedUntil) return state;
    const activePath = reduceInteractionPath(graph, currentPath, { type: "selectStage", stageId: action.stageId as never });
    return syncSelectionFromPath(topic, { ...state, activeStageId: action.stageId, lastIntent: "scroll" }, activePath);
  }

  if (action.type === "SELECT_STAGE") {
    const activePath = reduceInteractionPath(graph, currentPath, { type: "selectStage", stageId: action.stageId as never });
    return syncSelectionFromPath(topic, {
      ...state,
      activeStageId: action.stageId,
      lastIntent: "flow",
      lockedUntil: now + interactionLockMs,
    }, activePath);
  }

  if (action.type === "SELECT_EVIDENCE_SOURCE") {
    const activePath = resolveActivePathBySource(graph, action.source);
    return syncSelectionFromPath(topic, {
      ...state,
      lastIntent: "control",
      lockedUntil: now + interactionLockMs,
    }, activePath);
  }

  if (action.type === "SELECT_CLASSIFICATION_GROUP") {
    const activePath = resolveActivePath(graph, { stageId: "classify", subflowId: action.groupId });
    return syncSelectionFromPath(topic, { ...state, lastIntent: "control", lockedUntil: now + interactionLockMs }, activePath);
  }

  if (action.type === "SELECT_REPRESENTATIVE_OBJECT") {
    const object = topic.representativeObjects.find((item) => item.id === action.objectId);
    const activePath = resolveActivePath(graph, {
      stageId: "inspect",
      subflowId: object?.groupId,
      nodeId: action.objectId,
    });
    return syncSelectionFromPath(topic, { ...state, lastIntent: "control", lockedUntil: now + interactionLockMs }, activePath);
  }

  if (action.type === "SELECT_MECHANISM_STEP") {
    const activePath = resolveActivePath(graph, { stageId: "trace", subflowId: "mechanism", nodeId: action.stepId });
    return syncSelectionFromPath(topic, { ...state, lastIntent: "control", lockedUntil: now + interactionLockMs }, activePath);
  }

  if (action.type === "SELECT_SECONDARY_MECHANISM_STEP") {
    const activePath = resolveActivePath(graph, { stageId: "trace", subflowId: "secondaryMechanism", nodeId: action.stepId });
    return syncSelectionFromPath(topic, { ...state, lastIntent: "control", lockedUntil: now + interactionLockMs }, activePath);
  }

  if (action.type === "SELECT_COMPARE_PAIR") {
    const activePath = resolveActivePath(graph, { stageId: "compare", subflowId: action.pairId });
    return syncSelectionFromPath(topic, { ...state, lastIntent: "control", lockedUntil: now + interactionLockMs }, activePath);
  }

  if (action.type === "SELECT_COMPARE_SIDE") {
    const activePath = resolveActivePath(graph, { stageId: "compare", subflowId: action.pairId, nodeId: action.side });
    return syncSelectionFromPath(topic, { ...state, lastIntent: "control", lockedUntil: now + interactionLockMs }, activePath);
  }

  if (action.type === "SELECT_CLICK_TASK") {
    const activePath = resolveActivePath(graph, { stageId: "tasks", subflowId: action.taskId });
    return syncSelectionFromPath(topic, {
      ...state,
      activeStageId: "tasks",
      activeTaskId: action.taskId,
      lastIntent: "task",
      lockedUntil: now + interactionLockMs,
    }, activePath);
  }

  if (action.type === "CLICK_TASK_OPTION") {
    return applyTaskOptionClick(topic, state, locale, action.taskId, action.optionId, now);
  }

  return state;
}

export function resolveTopicPresentation(topic: Topic, state: TopicInteractionState, locale: Locale): TopicPresentation {
  const graph = getTopicInteractionGraph(topic, locale);
  const activePath = state.activePath ?? getDefaultActivePath(graph);
  const graphPresentation = resolveGraphPresentation(graph, activePath);
  const taskId = state.activeTaskId;
  const selectedIds = taskId ? state.taskSelectedIds[taskId] ?? [] : [];
  const result = taskId ? state.taskResults[taskId] : undefined;
  const activeSource = activePath.source ?? state.activeEvidenceSource;
  const evidenceSource = asEvidenceSource(activeSource);
  let evidence: VisualEvidenceState | null = null;

  if (evidenceSource?.includes("#")) {
    const baseSource = evidenceSource.split("#")[0] as EvidenceSourcePath;
    const baseEvidence = resolveVisualEvidence(topic, { source: baseSource, selectedIds, result, locale });
    if (baseEvidence && graphPresentation.evidence) {
      evidence = {
        ...baseEvidence,
        source: evidenceSource,
        sourceId: evidenceSource.split("#")[1] ?? baseEvidence.sourceId,
        status: activePath.status ?? result ?? baseEvidence.status,
        evidenceTitle: graphPresentation.evidence.title,
        evidenceCopy: graphPresentation.evidence.copy ?? baseEvidence.evidenceCopy,
        selectedLabels: [graphPresentation.evidence.title],
        focus: {
          ...baseEvidence.focus,
          mode: "compare-side",
          activeRegionIds: activePath.activeRegionIds,
          dimOthers: true,
        },
      };
    }
  } else if (evidenceSource) {
    evidence = resolveVisualEvidence(topic, {
      source: evidenceSource,
      selectedIds,
      result: activePath.status ?? result,
      locale,
    });
  }

  const visualSlot =
    (activePath.visualSlotId ? topic.visualSlots?.find((slot) => slot.id === activePath.visualSlotId) : null) ??
    (evidence ? topic.visualSlots?.find((slot) => slot.id === evidence.visualSlotId) ?? null : null);

  return {
    state: {
      ...state,
      activePath,
      activeVisualSlotId: visualSlot?.id ?? state.activeVisualSlotId,
    },
    activeStageId: activePath.stageId,
    evidence,
    visualSlot,
  };
}
