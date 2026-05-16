import type { ClickTask, EvidenceStatus, Topic, VisualEvidenceState, VisualSlot } from "../../../boards/kids-world/src/types/topic";
import { resolveVisualEvidence } from "./evidence";
import { normalizeFocus } from "./focus";
import { getVisualSlotForTarget } from "./visual-slots";

export type MainFlowStageId = "observe" | "classify" | "inspect" | "trace" | "compare" | "tasks" | "next";
export type SubflowKind =
  | "hero"
  | "classificationGroup"
  | "objectGroup"
  | "objectDetail"
  | "mechanism"
  | "secondaryMechanism"
  | "comparePair"
  | "clickTask"
  | "summary"
  | "parentGuide"
  | "relatedTopics"
  | "textOnly";
export type SecondaryNodeKind = "representativeObject" | "objectFeature" | "mechanismStep" | "compareSide" | "taskOption" | "summaryItem";
export type FocusMode = "whole" | "hotspot" | "group" | "path-step" | "sequence-progress" | "compare-side" | "task-option" | "zoom" | "callout" | "none";

export type VisualBinding = {
  source?: string;
  visualSlotId: string;
  assetId: string;
  focusMode: FocusMode;
  activeRegionIds: string[];
  target?: string;
  role?: "hero" | "object" | "mechanism" | "compare" | "task" | "parent" | "summary";
  required?: boolean;
};

export type EvidenceBinding = {
  source: string;
  title: string;
  copy?: string;
  hint?: string;
  successCopy?: string;
  wrongHint?: string;
};

export type SecondaryNode = {
  id: string;
  label: string;
  kind: SecondaryNodeKind;
  source: string;
  visual: VisualBinding | null;
  evidence?: EvidenceBinding | null;
  isCorrect?: boolean;
};

export type SubflowContainer = {
  id: string;
  label: string;
  kind: SubflowKind;
  source: string;
  type?: "singleChoice" | "findTarget" | "sequenceClick";
  visual: VisualBinding | null;
  visualPolicy?: "required" | "optional" | "text-only";
  defaultNodeId: string | null;
  nodes: SecondaryNode[];
};

export type MainFlowStage = {
  id: MainFlowStageId;
  label: string;
  intent: string;
  relationshipShape: string;
  defaultSource: string | null;
  defaultSubflowId: string | null;
  defaultNodeId: string | null;
  subflows: SubflowContainer[];
  inspectMode?: "object-detail-with-group-shell";
};

export type TopicInteractionGraph = {
  slug: string;
  title: string;
  expectedHierarchy: "mainFlowStage -> subflowContainer -> secondaryNode -> visual/evidence";
  stages: MainFlowStage[];
};

function slotVisual(slot: VisualSlot | null | undefined, source: string, focusMode: FocusMode = "whole", activeRegionIds: string[] = []): VisualBinding | null {
  if (!slot) return null;
  return {
    source,
    visualSlotId: slot.id,
    assetId: slot.assetId,
    focusMode,
    activeRegionIds,
    target: slot.target,
    role: slot.role === "observation" ? "object" : slot.role === "process" ? "mechanism" : slot.role === "task" ? "task" : slot.role,
    required: slot.required,
  };
}

function evidenceBinding(evidence: VisualEvidenceState | null | undefined, source: string, fallbackTitle: string): EvidenceBinding {
  return {
    source,
    title: evidence?.evidenceTitle ?? fallbackTitle,
    copy: evidence?.evidenceCopy,
    hint: evidence?.observePrompt,
  };
}

function visualForSource(topic: Topic, source: string, locale = "zh-CN"): VisualBinding | null {
  if (source.includes("#")) {
    const [baseSource, side] = source.split("#");
    const base = visualForSource(topic, baseSource, locale);
    if (!base) return null;
    return {
      ...base,
      source,
      focusMode: "compare-side",
      activeRegionIds: [side === "b" ? "right" : "left"],
    };
  }

  if (source === "hero") return slotVisual(getVisualSlotForTarget(topic, "hero"), source, "whole");
  if (source === "parentTips") return slotVisual(getVisualSlotForTarget(topic, "parentTips"), source, "whole");
  if (source.startsWith("clickTasks.") && !source.includes(".options.")) {
    const slot = getVisualSlotForTarget(topic, source) ?? getVisualSlotForTarget(topic, "clickTasks") ?? getVisualSlotForTarget(topic, "hero");
    return slotVisual(slot, source, "whole");
  }

  const evidence = resolveVisualEvidence(topic, { source: source as never, locale: locale === "en-US" ? "en-US" : "zh-CN" });
  if (!evidence) return null;
  const slot = topic.visualSlots?.find((item) => item.id === evidence.visualSlotId);
  if (!slot) return null;
  const focus = normalizeFocus(evidence.focus, evidence.sourceId);
  return {
    source,
    visualSlotId: slot.id,
    assetId: slot.assetId,
    focusMode: focus.focusMode,
    activeRegionIds: focus.activeRegionIds,
    target: slot.target,
    role: slot.role === "observation" ? "object" : slot.role === "process" ? "mechanism" : slot.role === "task" ? "task" : slot.role,
    required: slot.required,
  };
}

function evidenceForSource(topic: Topic, source: string, label: string, locale = "zh-CN"): EvidenceBinding {
  if (source.includes("#")) {
    const [pairSource, side] = source.split("#");
    const pairId = pairSource.split(".")[1];
    const pair = topic.comparePairs.find((item) => item.id === pairId);
    const sideData = side === "b" ? pair?.b : pair?.a;
    return {
      source,
      title: sideData?.name ?? label,
      copy: sideData?.points?.join("；"),
    };
  }
  const evidence = source === "hero" || source === "parentTips" || (source.startsWith("clickTasks.") && !source.includes(".options."))
    ? null
    : resolveVisualEvidence(topic, { source: source as never, locale: locale === "en-US" ? "en-US" : "zh-CN" });
  return evidenceBinding(evidence, source, label);
}

function taskOptions(task: ClickTask): Array<{ id: string; label: string; isCorrect?: boolean }> {
  const options = task.options ?? [...(task.targetIds ?? []), ...(task.decoyIds ?? [])].map((id) => ({ id, label: id.replace(/-/g, " ") }));
  return options.map((option) => ({
    ...option,
    isCorrect:
      task.type === "singleChoice"
        ? option.id === task.correctOptionId
        : task.type === "findTarget"
          ? task.targetIds?.includes(option.id) ?? false
          : task.correctSequence?.includes(option.id) ?? false,
  }));
}

function stage(id: MainFlowStageId, label: string, intent: string, relationshipShape: string, subflows: SubflowContainer[]): MainFlowStage {
  const defaultSubflow = subflows[0] ?? null;
  return {
    id,
    label,
    intent,
    relationshipShape,
    defaultSubflowId: defaultSubflow?.id ?? null,
    defaultNodeId: defaultSubflow?.defaultNodeId ?? null,
    defaultSource: defaultSubflow?.defaultNodeId
      ? defaultSubflow.nodes.find((node) => node.id === defaultSubflow.defaultNodeId)?.source ?? defaultSubflow.source
      : defaultSubflow?.source ?? null,
    subflows,
  };
}

export function getTopicInteractionGraph(topic: Topic, locale = "zh-CN"): TopicInteractionGraph {
  const objectsByGroup = new Map<string, Topic["representativeObjects"]>();
  for (const object of topic.representativeObjects) {
    const list = objectsByGroup.get(object.groupId) ?? [];
    list.push(object);
    objectsByGroup.set(object.groupId, list);
  }

  const stages: MainFlowStage[] = [
    stage("observe", "发现它", "先观察主题出现在哪里", "main-only", [
      {
        id: "hero",
        label: topic.hero.title,
        kind: "hero",
        source: "hero",
        visual: visualForSource(topic, "hero", locale),
        defaultNodeId: null,
        nodes: [],
      },
    ]),
    stage(
      "classify",
      "认出它",
      "识别主题中的类别",
      "main -> classification group -> representative objects",
      topic.classificationGroups.map((group) => {
        const nodes = (objectsByGroup.get(group.id) ?? []).map<SecondaryNode>((object) => ({
          id: object.id,
          label: object.name,
          kind: "representativeObject",
          source: `representativeObjects.${object.id}`,
          visual: visualForSource(topic, `representativeObjects.${object.id}`, locale),
          evidence: evidenceForSource(topic, `representativeObjects.${object.id}`, object.name, locale),
        }));
        return {
          id: group.id,
          label: group.name,
          kind: "classificationGroup",
          source: `classificationGroups.${group.id}`,
          visual: visualForSource(topic, `classificationGroups.${group.id}`, locale),
          defaultNodeId: null,
          nodes,
        };
      }),
    ),
    {
      ...stage(
        "inspect",
        "看懂它",
        "细看一个代表对象",
        "main -> object group -> representative objects",
        topic.classificationGroups.map((group) => {
          const nodes = (objectsByGroup.get(group.id) ?? []).map<SecondaryNode>((object) => ({
            id: object.id,
            label: object.name,
            kind: "representativeObject",
            source: `representativeObjects.${object.id}`,
            visual: visualForSource(topic, `representativeObjects.${object.id}`, locale),
            evidence: evidenceForSource(topic, `representativeObjects.${object.id}`, object.name, locale),
          }));
          return {
            id: group.id,
            label: group.name,
            kind: "objectGroup",
            source: `classificationGroups.${group.id}`,
            visual: visualForSource(topic, `classificationGroups.${group.id}`, locale),
            defaultNodeId: nodes[0]?.id ?? null,
            nodes,
          };
        }),
      ),
      inspectMode: "object-detail-with-group-shell",
    },
    stage("trace", "追踪它", "理解过程如何发生", "main -> mechanism container -> mechanism steps", [
      {
        id: "mechanism",
        label: topic.mechanism.title ?? "机制步骤",
        kind: "mechanism",
        source: "mechanism",
        visual: slotVisual(getVisualSlotForTarget(topic, "mechanism"), "mechanism", "whole"),
        defaultNodeId: topic.mechanism.steps[0]?.id ?? null,
        nodes: topic.mechanism.steps.map((step) => ({
          id: step.id,
          label: step.shortTitle,
          kind: "mechanismStep",
          source: `mechanism.steps.${step.id}`,
          visual: visualForSource(topic, `mechanism.steps.${step.id}`, locale),
          evidence: evidenceForSource(topic, `mechanism.steps.${step.id}`, step.shortTitle, locale),
        })),
      },
      ...(topic.secondaryMechanism
        ? [
            {
              id: "secondaryMechanism",
              label: topic.secondaryMechanism.title,
              kind: "secondaryMechanism" as const,
              source: "secondaryMechanism",
              visual: slotVisual(getVisualSlotForTarget(topic, "secondaryMechanism") ?? getVisualSlotForTarget(topic, "mechanism"), "secondaryMechanism", "whole"),
              defaultNodeId: topic.secondaryMechanism.steps[0]?.id ?? null,
              nodes: topic.secondaryMechanism.steps.map((step) => ({
                id: step.id,
                label: step.shortTitle,
                kind: "mechanismStep" as const,
                source: `secondaryMechanism.steps.${step.id}`,
                visual: visualForSource(topic, `secondaryMechanism.steps.${step.id}`, locale),
                evidence: evidenceForSource(topic, `secondaryMechanism.steps.${step.id}`, step.shortTitle, locale),
              })),
            },
          ]
        : []),
    ]),
    stage(
      "compare",
      "比一比",
      "区分容易混淆的概念",
      "main -> compare pair -> compared sides",
      topic.comparePairs.map((pair) => ({
        id: pair.id,
        label: pair.title,
        kind: "comparePair",
        source: `comparePairs.${pair.id}`,
        visual: visualForSource(topic, `comparePairs.${pair.id}`, locale),
        defaultNodeId: null,
        nodes: [
          {
            id: "a",
            label: pair.a.name,
            kind: "compareSide",
            source: `comparePairs.${pair.id}#a`,
            visual: visualForSource(topic, `comparePairs.${pair.id}#a`, locale),
            evidence: evidenceForSource(topic, `comparePairs.${pair.id}#a`, pair.a.name, locale),
          },
          {
            id: "b",
            label: pair.b.name,
            kind: "compareSide",
            source: `comparePairs.${pair.id}#b`,
            visual: visualForSource(topic, `comparePairs.${pair.id}#b`, locale),
            evidence: evidenceForSource(topic, `comparePairs.${pair.id}#b`, pair.b.name, locale),
          },
        ],
      })),
    ),
    stage(
      "tasks",
      "做任务",
      "通过点击任务进行判断",
      "main -> click task -> answer options",
      topic.clickTasks.map((task) => ({
        id: task.id,
        label: task.title,
        kind: "clickTask",
        source: `clickTasks.${task.id}`,
        type: task.type as "singleChoice" | "findTarget" | "sequenceClick",
        visual: visualForSource(topic, `clickTasks.${task.id}`, locale),
        defaultNodeId: null,
        nodes: taskOptions(task).map((option) => ({
          id: option.id,
          label: option.label,
          kind: "taskOption",
          source: `clickTasks.${task.id}.options.${option.id}`,
          visual: visualForSource(topic, `clickTasks.${task.id}.options.${option.id}`, locale),
          evidence: evidenceForSource(topic, `clickTasks.${task.id}.options.${option.id}`, option.label, locale),
          isCorrect: option.isCorrect,
        })),
      })),
    ),
    stage("next", "继续看", "表达和继续探索", "main -> summary/parent/related containers", [
      {
        id: "speak",
        label: "表达模板",
        kind: "summary",
        source: "speakTemplates",
        visual: null,
        visualPolicy: "text-only",
        defaultNodeId: null,
        nodes: [],
      },
      {
        id: "parent",
        label: "家长提示",
        kind: "parentGuide",
        source: "parentTips",
        visual: visualForSource(topic, "parentTips", locale),
        visualPolicy: getVisualSlotForTarget(topic, "parentTips") ? "optional" : "text-only",
        defaultNodeId: null,
        nodes: [],
      },
      {
        id: "related",
        label: "相关主题",
        kind: "relatedTopics",
        source: "relatedTopics",
        visual: null,
        visualPolicy: "text-only",
        defaultNodeId: null,
        nodes: [],
      },
    ]),
  ];

  return {
    slug: topic.slug,
    title: topic.title,
    expectedHierarchy: "mainFlowStage -> subflowContainer -> secondaryNode -> visual/evidence",
    stages,
  };
}

export function getStageById(graph: TopicInteractionGraph, stageId: MainFlowStageId): MainFlowStage | null {
  return graph.stages.find((stageItem) => stageItem.id === stageId) ?? null;
}

export function findNodeBySource(graph: TopicInteractionGraph, source: string) {
  for (const stageItem of graph.stages) {
    for (const subflow of stageItem.subflows) {
      if (subflow.source === source) return { stage: stageItem, subflow, node: null };
      const node = subflow.nodes.find((item) => item.source === source);
      if (node) return { stage: stageItem, subflow, node };
    }
  }
  return null;
}

export function taskResultForOption(task: ClickTask, optionId: string, selectedIds: string[] = []): EvidenceStatus {
  if (task.type === "singleChoice") return optionId === task.correctOptionId ? "correct" : "wrong";
  if (task.type === "findTarget") {
    if (!task.targetIds?.includes(optionId)) return "wrong";
    const next = new Set([...selectedIds, optionId]);
    return task.targetIds.every((id) => next.has(id)) ? "complete" : "partial";
  }
  if (task.type === "sequenceClick") {
    const expected = task.correctSequence?.[selectedIds.length];
    if (optionId !== expected) return "wrong";
    return selectedIds.length + 1 === task.correctSequence?.length ? "complete" : "partial";
  }
  return "selected";
}
