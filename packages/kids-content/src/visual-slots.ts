import type {
  EvidenceSourcePath,
  LearningFlowStage,
  Locale,
  Topic,
  VisualSlot,
  VisualSlotRole,
  VisualSlotTarget,
} from "../../../boards/kids-world/src/types/topic";

const zhFlowCopy = {
  observe: ["发现它", "我们先看看它在哪里出现。"],
  classify: ["认出它", "看看它属于哪一类。"],
  inspect: ["看懂它", "找一找关键对象和线索。"],
  trace: ["追踪它", "按顺序看看变化怎么发生。"],
  compare: ["比一比", "和相似对象放在一起比较。"],
  tasks: ["做任务", "试试看能不能自己判断。"],
  next: ["继续看", "把发现说出来，再去探索相关主题。"],
} as const;

const enFlowCopy = {
  observe: ["Spot it", "Start with where it appears."],
  classify: ["Name it", "See which group it belongs to."],
  inspect: ["Read it", "Look for key objects and clues."],
  trace: ["Trace it", "Follow the changes in order."],
  compare: ["Compare", "Put similar things side by side."],
  tasks: ["Try it", "Check if you can decide on your own."],
  next: ["Keep going", "Say what you found, then explore nearby topics."],
} as const;

function stage(
  id: keyof typeof zhFlowCopy,
  locale: Locale,
  sectionIds: string[],
  visualSlotId?: string,
  defaultEvidenceSource?: EvidenceSourcePath,
): LearningFlowStage {
  const copy = locale === "zh-CN" ? zhFlowCopy[id] : enFlowCopy[id];
  return {
    id,
    label: copy[0],
    sectionIds,
    visualSlotId,
    childPrompt: copy[1],
    defaultEvidenceSource,
  };
}

export function getTopicVisualSlots(topic: Pick<Topic, "visualSlots">): VisualSlot[] {
  return topic.visualSlots ?? [];
}

export function getVisualSlotForTarget(
  topic: Pick<Topic, "visualSlots">,
  target: VisualSlotTarget | string,
): VisualSlot | null {
  const slots = getTopicVisualSlots(topic);
  const exact = slots.find((slot) => slot.target === target);
  if (exact) return exact;

  const baseTarget = target.split(".")[0];
  return slots.find((slot) => slot.target === baseTarget) ?? null;
}

export function getVisualSlotsForRole(topic: Pick<Topic, "visualSlots">, role: VisualSlotRole): VisualSlot[] {
  return getTopicVisualSlots(topic).filter((slot) => slot.role === role);
}

export function getDefaultEvidenceSourceForStage(topic: Topic, stageId: string): EvidenceSourcePath | undefined {
  if (stageId === "classify") {
    const first = topic.classificationGroups[0];
    return first ? (`classificationGroups.${first.id}` as EvidenceSourcePath) : undefined;
  }

  if (stageId === "inspect") {
    const first = topic.representativeObjects[0];
    return first ? (`representativeObjects.${first.id}` as EvidenceSourcePath) : undefined;
  }

  if (stageId === "trace") {
    const first = topic.mechanism.steps[0];
    return first ? (`mechanism.steps.${first.id}` as EvidenceSourcePath) : undefined;
  }

  if (stageId === "compare") {
    const first = topic.comparePairs[0];
    return first ? (`comparePairs.${first.id}` as EvidenceSourcePath) : undefined;
  }

  if (stageId === "tasks") {
    const first = topic.clickTasks[0];
    return first ? (`clickTasks.${first.id}` as EvidenceSourcePath) : undefined;
  }

  return undefined;
}

export function getTopicLearningFlow(topic: Topic, locale: Locale): LearningFlowStage[] {
  if (topic.learningFlow?.length) return topic.learningFlow;

  const slots = getTopicVisualSlots(topic);
  const slotForTarget = (target: VisualSlotTarget) => slots.find((slot) => slot.target === target)?.id;
  const stages: LearningFlowStage[] = [
    stage("observe", locale, ["topic-hero", "topic-observe"], slotForTarget("hero")),
    stage("classify", locale, ["topic-classification"], slotForTarget("classificationGroups"), getDefaultEvidenceSourceForStage(topic, "classify")),
    stage("inspect", locale, ["topic-objects"], slotForTarget("representativeObjects"), getDefaultEvidenceSourceForStage(topic, "inspect")),
    stage("trace", locale, ["topic-mechanism", "topic-secondary-mechanism"], slotForTarget("mechanism"), getDefaultEvidenceSourceForStage(topic, "trace")),
  ];

  if (topic.comparePairs.length > 0) {
    stages.push(stage("compare", locale, ["topic-compare"], slotForTarget("comparePairs"), getDefaultEvidenceSourceForStage(topic, "compare")));
  }

  if (topic.clickTasks.length > 0) {
    stages.push(stage("tasks", locale, ["topic-tasks"], slotForTarget("clickTasks"), getDefaultEvidenceSourceForStage(topic, "tasks")));
  }

  stages.push(stage("next", locale, ["topic-speak", "topic-parent", "topic-related"], undefined));
  return stages;
}
