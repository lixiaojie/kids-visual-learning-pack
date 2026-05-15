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
import { getDefaultEvidenceSourceForStage, getTopicLearningFlow } from "./visual-slots";

export type TopicInteractionState = {
  activeStageId: string;
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
  const stages = getTopicLearningFlow(topic, locale);
  const firstStage = stages[0];
  const firstInteractiveStage = stages.find((item) => item.defaultEvidenceSource);
  const activeStageId = firstStage?.id ?? "";
  const activeEvidenceSource =
    firstStage?.defaultEvidenceSource ??
    firstInteractiveStage?.defaultEvidenceSource ??
    getDefaultEvidenceSourceForStage(topic, firstInteractiveStage?.id ?? activeStageId);

  return syncSelectionFromSource(topic, {
    activeStageId,
    activeEvidenceSource,
    taskSelectedIds: {},
    taskResults: {},
    taskMessages: {},
    lastIntent: "init",
  });
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

  return syncSelectionFromSource(topic, {
    ...state,
    activeTaskId: taskId,
    activeEvidenceSource: `clickTasks.${taskId}.options.${optionId}` as EvidenceSourcePath,
    taskSelectedIds: { ...state.taskSelectedIds, [taskId]: nextSelected },
    taskResults: { ...state.taskResults, [taskId]: nextResult },
    taskMessages: { ...state.taskMessages, [taskId]: message },
    lastIntent: "task",
    lockedUntil: now + interactionLockMs,
  });
}

export function reduceTopicInteractionState(
  topic: Topic,
  locale: Locale,
  state: TopicInteractionState,
  action: TopicInteractionAction,
): TopicInteractionState {
  const now = "now" in action && action.now ? action.now : Date.now();

  if (action.type === "RESET_TOPIC") {
    return createInitialTopicInteractionState(action.topic, action.locale);
  }

  if (action.type === "SCROLL_STAGE_VISIBLE") {
    if (state.lockedUntil && now < state.lockedUntil) return state;
    return { ...state, activeStageId: action.stageId, lastIntent: "scroll" };
  }

  if (action.type === "SELECT_STAGE") {
    const source = getDefaultEvidenceSourceForStage(topic, action.stageId);
    return syncSelectionFromSource(topic, {
      ...state,
      activeStageId: action.stageId,
      activeEvidenceSource: source ?? state.activeEvidenceSource,
      lastIntent: "flow",
      lockedUntil: now + interactionLockMs,
    });
  }

  if (action.type === "SELECT_EVIDENCE_SOURCE") {
    return syncSelectionFromSource(topic, {
      ...state,
      activeEvidenceSource: action.source,
      lastIntent: "control",
      lockedUntil: now + interactionLockMs,
    });
  }

  if (action.type === "SELECT_CLASSIFICATION_GROUP") {
    return reduceTopicInteractionState(topic, locale, state, {
      type: "SELECT_EVIDENCE_SOURCE",
      source: `classificationGroups.${action.groupId}` as EvidenceSourcePath,
      now,
    });
  }

  if (action.type === "SELECT_REPRESENTATIVE_OBJECT") {
    return reduceTopicInteractionState(topic, locale, state, {
      type: "SELECT_EVIDENCE_SOURCE",
      source: `representativeObjects.${action.objectId}` as EvidenceSourcePath,
      now,
    });
  }

  if (action.type === "SELECT_MECHANISM_STEP") {
    return reduceTopicInteractionState(topic, locale, state, {
      type: "SELECT_EVIDENCE_SOURCE",
      source: `mechanism.steps.${action.stepId}` as EvidenceSourcePath,
      now,
    });
  }

  if (action.type === "SELECT_SECONDARY_MECHANISM_STEP") {
    return reduceTopicInteractionState(topic, locale, state, {
      type: "SELECT_EVIDENCE_SOURCE",
      source: `secondaryMechanism.steps.${action.stepId}` as EvidenceSourcePath,
      now,
    });
  }

  if (action.type === "SELECT_COMPARE_PAIR") {
    return reduceTopicInteractionState(topic, locale, state, {
      type: "SELECT_EVIDENCE_SOURCE",
      source: `comparePairs.${action.pairId}` as EvidenceSourcePath,
      now,
    });
  }

  if (action.type === "SELECT_CLICK_TASK") {
    return syncSelectionFromSource(topic, {
      ...state,
      activeStageId: "tasks",
      activeTaskId: action.taskId,
      activeEvidenceSource: `clickTasks.${action.taskId}` as EvidenceSourcePath,
      lastIntent: "task",
      lockedUntil: now + interactionLockMs,
    });
  }

  if (action.type === "CLICK_TASK_OPTION") {
    return applyTaskOptionClick(topic, state, locale, action.taskId, action.optionId, now);
  }

  return state;
}

export function resolveTopicPresentation(topic: Topic, state: TopicInteractionState, locale: Locale): TopicPresentation {
  const taskId = state.activeTaskId;
  const selectedIds = taskId ? state.taskSelectedIds[taskId] ?? [] : [];
  const result = taskId ? state.taskResults[taskId] : undefined;
  const evidence = state.activeEvidenceSource
    ? resolveVisualEvidence(topic, {
        source: state.activeEvidenceSource,
        selectedIds,
        result,
        locale,
      })
    : null;
  const visualSlot = evidence ? topic.visualSlots?.find((slot) => slot.id === evidence.visualSlotId) ?? null : null;

  return {
    state: {
      ...state,
      activeVisualSlotId: visualSlot?.id ?? state.activeVisualSlotId,
    },
    activeStageId: state.activeStageId,
    evidence,
    visualSlot,
  };
}
