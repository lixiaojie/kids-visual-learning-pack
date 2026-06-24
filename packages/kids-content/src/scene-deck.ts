import type {
  ClickTask,
  ContentBlock,
  EvidenceSourcePath,
  EvidenceStatus,
  FocusItem,
  LearningScene,
  LayoutPreset,
  Locale,
  SceneEvidenceSource,
  SceneTask,
  SceneTaskOption,
  SceneType,
  SceneVisualPlan,
  SceneVisualRegion,
  Topic,
  VisualEvidenceState,
  VisualFocusRegion,
  VisualSlot,
} from "../../../boards/kids-world/src/types/topic";
import { getKnowledgeTopicAssetId } from "./assets";
import { resolveVisualEvidence } from "./evidence";
import { getGeneratedImageUrl } from "./media";
import { getVisualSlotForTarget } from "./visual-slots";

export type NormalizeTopicToSceneDeckOptions = {
  locale: Locale;
  cdnBase?: string;
};

export type SceneVisualViewModel = {
  assetId: string;
  url?: string;
  alt: string;
  caption?: string;
  aspectRatio: SceneVisualPlan["aspectRatio"];
  regions: SceneVisualRegion[];
};

export type FocusItemViewModel = FocusItem;
export type ContentBlockViewModel = ContentBlock;
export type SceneTaskViewModel = SceneTask;

export type SceneViewModel = {
  id: string;
  order: number;
  title: string;
  kidQuestion: string;
  sceneType: SceneType;
  navLabel: string;
  visual: SceneVisualViewModel;
  focusItems: FocusItemViewModel[];
  contentBlocks: ContentBlockViewModel[];
  tasks: SceneTaskViewModel[];
  speakPrompts: string[];
  parentTips: string[];
};

export type SceneDeckViewModel = {
  topic: {
    slug: string;
    title: string;
    subtitle: string;
    coreQuestion: string;
    ageRange?: string;
  };
  scenes: SceneViewModel[];
};

export type SceneTaskState = {
  taskId: string;
  selectedOptionIds: string[];
  result: EvidenceStatus;
  feedbackMessage: string;
};

export type SceneInteractionState = {
  activeSceneId: string;
  activeFocusSourceByScene: Record<string, SceneEvidenceSource>;
  taskStateByTaskId: Record<string, SceneTaskState>;
  lastIntent: "init" | "scene-nav" | "scroll" | "focus-select" | "task";
  scrollLockUntil?: number;
};

export type SceneInteractionAction =
  | { type: "SELECT_SCENE"; sceneId: string; now?: number }
  | { type: "SCROLL_SCENE_VISIBLE"; sceneId: string; now?: number }
  | { type: "SELECT_FOCUS"; sceneId: string; source: SceneEvidenceSource; now?: number }
  | { type: "CLICK_TASK_OPTION"; sceneId: string; taskId: string; optionId: string; now?: number };

export type ResolvedSceneEvidence = {
  source: SceneEvidenceSource;
  focusItem?: FocusItemViewModel;
  task?: SceneTaskViewModel;
  taskOption?: SceneTaskOption;
  regionIds: string[];
  evidenceTitle: string;
  observePrompt?: string;
  evidenceCopy: string;
  status: EvidenceStatus | "notice";
};

export type ScenePresentation = {
  activeScene: SceneViewModel;
  activeFocusSource?: SceneEvidenceSource;
  activeEvidence?: ResolvedSceneEvidence;
  taskStateByTaskId: Record<string, SceneTaskState>;
};

const scrollLockMs = 450;

function sourceId(source: string): string {
  if (source.includes("#")) return source.split("#")[1] ?? source;
  const parts = source.split(".");
  return parts[parts.length - 1] ?? source;
}

function asEvidenceSource(source: string): EvidenceSourcePath | null {
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

function normalizeCoord(value: number): number {
  const scaled = value <= 1 ? value * 1000 : value;
  return Math.max(0, Math.min(1000, Math.round(scaled)));
}

function regionFromFocusRegion(region: VisualFocusRegion): SceneVisualRegion {
  return {
    id: region.id,
    entityIds: [region.id],
    label: region.label ?? region.id,
    shape: "rect",
    bounds: {
      x: normalizeCoord(region.x),
      y: normalizeCoord(region.y),
      w: normalizeCoord(region.width),
      h: normalizeCoord(region.height),
    },
    minTapSize: 64,
  };
}

function fallbackRegion(id: string, label: string): SceneVisualRegion {
  return {
    id,
    entityIds: [id],
    label,
    shape: "rect",
    bounds: { x: 80, y: 120, w: 840, h: 680 },
    minTapSize: 64,
  };
}

function visualPlanForSlot(
  topic: Topic,
  id: string,
  sceneType: SceneType,
  layoutPreset: LayoutPreset,
  imageRole: SceneVisualPlan["imageRole"],
  slot: VisualSlot | null,
  regions: SceneVisualRegion[],
): SceneVisualPlan {
  const assetId = slot?.assetId ?? getKnowledgeTopicAssetId({ slug: topic.slug }) ?? "";
  return {
    id: `vp-${topic.slug}-${id}`,
    assetId,
    layoutPreset,
    imageRole,
    aspectRatio: "16:9",
    compositionZones: [],
    visualEntities: regions.map((region) => ({
      id: region.entityIds[0] ?? region.id,
      label: region.label,
      required: true,
    })),
    regions,
  };
}

function focusFromEvidence(topic: Topic, source: EvidenceSourcePath, locale: Locale): { focusItem: FocusItem; regions: SceneVisualRegion[] } | null {
  const evidence = resolveVisualEvidence(topic, { source, locale });
  if (!evidence) return null;
  const regions = evidence.focus?.regions?.map(regionFromFocusRegion) ?? [];
  const activeRegionIds = evidence.focus?.activeRegionIds?.length ? evidence.focus.activeRegionIds : [evidence.sourceId];

  for (const regionId of activeRegionIds) {
    if (!regions.some((region) => region.id === regionId)) {
      regions.push(fallbackRegion(regionId, evidence.selectedLabels?.[0] ?? evidence.evidenceTitle));
    }
  }

  return {
    focusItem: {
      id: `focus-${sourceId(source)}`,
      source,
      label: evidence.evidenceTitle,
      shortLabel: evidence.selectedLabels?.[0],
      regionIds: activeRegionIds,
      entityIds: activeRegionIds,
      evidenceTitle: evidence.evidenceTitle,
      observePrompt: evidence.observePrompt ?? "",
      evidenceCopy: evidence.evidenceCopy,
      markerChips: evidence.markerChips?.map((chip) => chip.label),
      expectedStatus: evidence.status === "selected" || evidence.status === "idle" ? "notice" : evidence.status,
      nextPrompt: evidence.nextPrompt,
    },
    regions,
  };
}

function uniqueRegions(items: Array<SceneVisualRegion[]>): SceneVisualRegion[] {
  const byId = new Map<string, SceneVisualRegion>();
  for (const regions of items) {
    for (const region of regions) {
      if (!byId.has(region.id)) byId.set(region.id, region);
    }
  }
  return [...byId.values()];
}

function sceneFromParts(
  topic: Topic,
  options: NormalizeTopicToSceneDeckOptions,
  input: {
    id: string;
    order: number;
    title: string;
    kidQuestion: string;
    sceneType: SceneType;
    layoutPreset: LayoutPreset;
    imageRole: SceneVisualPlan["imageRole"];
    slot: VisualSlot | null;
    sources: EvidenceSourcePath[];
    contentBlocks: ContentBlock[];
    tasks?: SceneTask[];
    speakPrompts?: string[];
    parentTips?: string[];
  },
): SceneViewModel {
  const resolved = input.sources
    .map((source) => focusFromEvidence(topic, source, options.locale))
    .filter((item): item is NonNullable<typeof item> => Boolean(item));
  let regions = uniqueRegions(resolved.map((item) => item.regions));
  const focusItems = resolved.map((item) => item.focusItem);

  if (regions.length === 0) {
    regions = [fallbackRegion(`region-${input.id}`, input.title)];
  }

  const visualPlan = visualPlanForSlot(topic, input.id, input.sceneType, input.layoutPreset, input.imageRole, input.slot, regions);
  return normalizeScene(topic, {
    id: input.id,
    order: input.order,
    title: input.title,
    kidQuestion: input.kidQuestion,
    sceneType: input.sceneType,
    visualPlan,
    focusItems,
    contentBlocks: input.contentBlocks,
    tasks: input.tasks,
    speakPrompts: input.speakPrompts,
    parentTips: input.parentTips,
  }, options);
}

function taskOptions(task: ClickTask): Array<{ id: string; label: string }> {
  return (
    task.options ??
    [...(task.targetIds ?? []), ...(task.decoyIds ?? [])].map((id) => ({
      id,
      label: id.replace(/-/g, " "),
    }))
  );
}

function normalizedTask(topic: Topic, task: ClickTask, locale: Locale): SceneTask {
  const options = taskOptions(task).map<SceneTaskOption>((option) => {
    const source = `clickTasks.${task.id}.options.${option.id}` as EvidenceSourcePath;
    const evidence = focusFromEvidence(topic, source, locale);
    const isCorrect =
      task.type === "singleChoice"
        ? option.id === task.correctOptionId
        : task.type === "findTarget"
          ? task.targetIds?.includes(option.id) ?? false
          : task.correctSequence?.includes(option.id) ?? false;

    return {
      id: option.id,
      label: option.label,
      source,
      regionIds: evidence?.focusItem.regionIds ?? [],
      isCorrect,
      notVisualReason: evidence ? undefined : "No visual evidence binding exists for this legacy option.",
    };
  });

  const correctRegions = options.filter((option) => option.isCorrect).flatMap((option) => option.regionIds);
  const decoyRegions = options.filter((option) => !option.isCorrect).flatMap((option) => option.regionIds);
  return {
    id: task.id,
    type: task.type === "findTarget" || task.type === "sequenceClick" ? task.type : "singleChoice",
    title: task.title,
    prompt: task.prompt ?? task.title,
    source: `clickTasks.${task.id}`,
    options,
    targetRegionIds: correctRegions,
    decoyRegionIds: decoyRegions,
    correctSequence: task.correctSequence,
    feedback: {
      correct: task.successCopy ?? (locale === "en-US" ? "Correct." : "答对了。"),
      wrong: task.wrongHint ?? (locale === "en-US" ? "Look again and try once more." : "再观察一下试试看。"),
      partial: task.prompt ?? task.title,
      complete: task.successCopy ?? (locale === "en-US" ? "All found." : "全部找到了。"),
    },
  };
}

function legacyFallbackScenes(topic: Topic, options: NormalizeTopicToSceneDeckOptions): SceneViewModel[] {
  const firstGroup = topic.classificationGroups[0];
  const firstObject = topic.representativeObjects[0];
  const firstStep = topic.mechanism.steps[0];
  const firstPair = topic.comparePairs[0];
  const firstTask = topic.clickTasks[0];
  const taskViewModels = topic.clickTasks.map((task) => normalizedTask(topic, task, options.locale));

  return [
    sceneFromParts(topic, options, {
      id: "scene-entry",
      order: 1,
      title: options.locale === "en-US" ? "First Look" : "先发现",
      kidQuestion: topic.coreQuestion,
      sceneType: "entry-scene",
      layoutPreset: "single-focus-scene",
      imageRole: "hero",
      slot: getVisualSlotForTarget(topic, "hero"),
      sources: [],
      contentBlocks: [{ id: "copy-entry", type: "short-explanation", body: topic.hero.sceneExplanation }],
    }),
    sceneFromParts(topic, options, {
      id: "scene-classify",
      order: 2,
      title: options.locale === "en-US" ? "Sort and Spot" : "分一分",
      kidQuestion: options.locale === "en-US" ? "Which group does it belong to?" : "它属于哪一类？",
      sceneType: "taxonomy-map",
      layoutPreset: "taxonomy-map",
      imageRole: "scene",
      slot: getVisualSlotForTarget(topic, "classificationGroups") ?? getVisualSlotForTarget(topic, "representativeObjects"),
      sources: [
        ...(firstGroup ? [`classificationGroups.${firstGroup.id}` as EvidenceSourcePath] : []),
        ...topic.representativeObjects.map((object) => `representativeObjects.${object.id}` as EvidenceSourcePath),
      ],
      contentBlocks: [
        {
          id: "copy-classify",
          type: "detail-list",
          title: options.locale === "en-US" ? "Representative objects" : "代表对象",
          items: topic.representativeObjects.map((object) => `${object.name}: ${object.childExplanation}`),
        },
      ],
    }),
    sceneFromParts(topic, options, {
      id: "scene-process",
      order: 3,
      title: options.locale === "en-US" ? "Watch Change" : "看变化",
      kidQuestion: options.locale === "en-US" ? "How does it happen step by step?" : "它是怎样一步步发生的？",
      sceneType: "process-path",
      layoutPreset: "process-path",
      imageRole: "process",
      slot: getVisualSlotForTarget(topic, "mechanism"),
      sources: [
        ...(firstStep ? topic.mechanism.steps.map((step) => `mechanism.steps.${step.id}` as EvidenceSourcePath) : []),
        ...(topic.secondaryMechanism?.steps ?? []).map((step) => `secondaryMechanism.steps.${step.id}` as EvidenceSourcePath),
      ],
      contentBlocks: [
        {
          id: "copy-process",
          type: "detail-list",
          title: topic.mechanism.title,
          items: topic.mechanism.steps.map((step) => `${step.shortTitle}: ${step.childExplanation}`),
        },
      ],
    }),
    sceneFromParts(topic, options, {
      id: "scene-compare",
      order: 4,
      title: options.locale === "en-US" ? "Compare" : "比一比",
      kidQuestion: options.locale === "en-US" ? "What is the same, and what is different?" : "哪里相同，哪里不同？",
      sceneType: "compare-split",
      layoutPreset: "compare-split",
      imageRole: "compare",
      slot: getVisualSlotForTarget(topic, "comparePairs"),
      sources: firstPair ? topic.comparePairs.map((pair) => `comparePairs.${pair.id}` as EvidenceSourcePath) : [],
      contentBlocks: [
        {
          id: "copy-compare",
          type: "detail-list",
          items: topic.comparePairs.map((pair) => `${pair.title}: ${pair.childConclusion}`),
        },
      ],
    }),
    sceneFromParts(topic, options, {
      id: "scene-task",
      order: 5,
      title: options.locale === "en-US" ? "Try It" : "点一点",
      kidQuestion: options.locale === "en-US" ? "Can you find the right answer?" : "你能找对吗？",
      sceneType: "task-board",
      layoutPreset: "task-board",
      imageRole: "task",
      slot: getVisualSlotForTarget(topic, firstTask ? `clickTasks.${firstTask.id}` : "clickTasks") ?? getVisualSlotForTarget(topic, "clickTasks"),
      sources: topic.clickTasks.flatMap((task) => taskOptions(task).map((option) => `clickTasks.${task.id}.options.${option.id}` as EvidenceSourcePath)),
      contentBlocks: [{ id: "copy-task", type: "short-explanation", body: firstTask?.prompt ?? firstTask?.title ?? "" }],
      tasks: taskViewModels,
    }),
    sceneFromParts(topic, options, {
      id: "scene-summary",
      order: 6,
      title: options.locale === "en-US" ? "Tell It Back" : "讲出来",
      kidQuestion: options.locale === "en-US" ? "Can you explain it to your parent?" : "你能讲给家长听吗？",
      sceneType: "summary-talk",
      layoutPreset: "summary-talk",
      imageRole: "summary",
      slot: getVisualSlotForTarget(topic, "parentTips") ?? getVisualSlotForTarget(topic, "hero"),
      sources: firstObject ? [`representativeObjects.${firstObject.id}` as EvidenceSourcePath] : [],
      contentBlocks: [
        {
          id: "copy-summary",
          type: "prompt-list",
          items: topic.speakTemplates,
        },
      ],
      speakPrompts: topic.speakTemplates,
      parentTips: topic.parentTips,
    }),
  ];
}

function normalizeScene(topic: Topic, scene: LearningScene, options: NormalizeTopicToSceneDeckOptions): SceneViewModel {
  return {
    id: scene.id,
    order: scene.order,
    title: scene.title,
    kidQuestion: scene.kidQuestion,
    sceneType: scene.sceneType,
    navLabel: `${scene.order}. ${scene.title}`,
    visual: {
      assetId: scene.visualPlan.assetId,
      url: getGeneratedImageUrl(scene.visualPlan.assetId, options.cdnBase),
      alt: scene.visualPlan.visualEntities[0]?.label ?? topic.title,
      aspectRatio: scene.visualPlan.aspectRatio,
      regions: scene.visualPlan.regions,
    },
    focusItems: scene.focusItems,
    contentBlocks: scene.contentBlocks,
    tasks: scene.tasks ?? [],
    speakPrompts: scene.speakPrompts ?? [],
    parentTips: scene.parentTips ?? [],
  };
}

export function normalizeTopicToSceneDeck(topic: Topic, options: NormalizeTopicToSceneDeckOptions): SceneDeckViewModel {
  const scenes = topic.learningScenes?.length
    ? topic.learningScenes
        .slice()
        .sort((a, b) => a.order - b.order)
        .map((scene) => normalizeScene(topic, scene, options))
    : legacyFallbackScenes(topic, options);

  return {
    topic: {
      slug: topic.slug,
      title: topic.title,
      subtitle: topic.subtitle,
      coreQuestion: topic.coreQuestion,
    },
    scenes,
  };
}

export function createInitialSceneInteractionState(deck: SceneDeckViewModel): SceneInteractionState {
  const firstScene = deck.scenes[0];
  const activeFocusSourceByScene: Record<string, SceneEvidenceSource> = {};
  for (const scene of deck.scenes) {
    const firstSource = scene.focusItems[0]?.source ?? scene.tasks[0]?.source;
    if (firstSource) activeFocusSourceByScene[scene.id] = firstSource;
  }

  return {
    activeSceneId: firstScene?.id ?? "",
    activeFocusSourceByScene,
    taskStateByTaskId: {},
    lastIntent: "init",
  };
}

function optionResult(task: SceneTask, option: SceneTaskOption, selectedIds: string[]): EvidenceStatus {
  if (task.type === "singleChoice") return option.isCorrect ? "correct" : "wrong";
  if (task.type === "findTarget") {
    if (!option.isCorrect) return "wrong";
    const next = new Set([...selectedIds, option.id]);
    return task.options.filter((item) => item.isCorrect).every((item) => next.has(item.id)) ? "complete" : "partial";
  }
  const expected = task.correctSequence?.[selectedIds.length];
  if (option.id !== expected) return "wrong";
  return selectedIds.length + 1 === task.correctSequence?.length ? "complete" : "partial";
}

function feedbackFor(task: SceneTask, result: EvidenceStatus): string {
  if (result === "correct") return task.feedback.correct;
  if (result === "complete") return task.feedback.complete ?? task.feedback.correct;
  if (result === "partial") return task.feedback.partial ?? task.prompt;
  if (result === "wrong") return task.feedback.wrong;
  return task.prompt;
}

export function reduceSceneInteractionState(
  deck: SceneDeckViewModel,
  state: SceneInteractionState,
  action: SceneInteractionAction,
): SceneInteractionState {
  const now = "now" in action && action.now ? action.now : Date.now();

  if (action.type === "SELECT_SCENE") {
    const scene = deck.scenes.find((item) => item.id === action.sceneId);
    if (!scene) return state;
    return {
      ...state,
      activeSceneId: scene.id,
      activeFocusSourceByScene: {
        ...state.activeFocusSourceByScene,
        [scene.id]: state.activeFocusSourceByScene[scene.id] ?? scene.focusItems[0]?.source ?? scene.tasks[0]?.source ?? "",
      },
      lastIntent: "scene-nav",
      scrollLockUntil: now + scrollLockMs,
    };
  }

  if (action.type === "SCROLL_SCENE_VISIBLE") {
    if (state.scrollLockUntil && now < state.scrollLockUntil) return state;
    return { ...state, activeSceneId: action.sceneId, lastIntent: "scroll" };
  }

  if (action.type === "SELECT_FOCUS") {
    return {
      ...state,
      activeFocusSourceByScene: { ...state.activeFocusSourceByScene, [action.sceneId]: action.source },
      lastIntent: "focus-select",
    };
  }

  if (action.type === "CLICK_TASK_OPTION") {
    const scene = deck.scenes.find((item) => item.id === action.sceneId);
    const task = scene?.tasks.find((item) => item.id === action.taskId);
    const option = task?.options.find((item) => item.id === action.optionId);
    if (!scene || !task || !option) return state;
    const previous = state.taskStateByTaskId[task.id]?.selectedOptionIds ?? [];
    const result = optionResult(task, option, previous);
    const selectedOptionIds =
      result === "wrong"
        ? [option.id]
        : task.type === "singleChoice"
          ? [option.id]
          : Array.from(new Set([...previous, option.id]));
    return {
      ...state,
      activeFocusSourceByScene: { ...state.activeFocusSourceByScene, [scene.id]: option.source },
      taskStateByTaskId: {
        ...state.taskStateByTaskId,
        [task.id]: {
          taskId: task.id,
          selectedOptionIds,
          result,
          feedbackMessage: feedbackFor(task, result),
        },
      },
      lastIntent: "task",
    };
  }

  return state;
}

export function resolveSceneEvidence(
  deck: SceneDeckViewModel,
  sceneId: string,
  source: SceneEvidenceSource,
): ResolvedSceneEvidence | null {
  const scene = deck.scenes.find((item) => item.id === sceneId);
  if (!scene) return null;
  const focusItem = scene.focusItems.find((item) => item.source === source);
  if (focusItem) {
    return {
      source,
      focusItem,
      regionIds: focusItem.regionIds,
      evidenceTitle: focusItem.evidenceTitle,
      observePrompt: focusItem.observePrompt,
      evidenceCopy: focusItem.evidenceCopy,
      status: focusItem.expectedStatus ?? "notice",
    };
  }

  for (const task of scene.tasks) {
    const taskOption = task.options.find((option) => option.source === source);
    if (taskOption) {
      return {
        source,
        task,
        taskOption,
        regionIds: taskOption.regionIds,
        evidenceTitle: taskOption.label,
        observePrompt: task.prompt,
        evidenceCopy: task.prompt,
        status: taskOption.isCorrect ? "correct" : "wrong",
      };
    }
  }

  const legacySource = asEvidenceSource(source);
  if (legacySource) {
    const sceneFocusItem = scene.focusItems.find((item) => item.source === legacySource);
    if (sceneFocusItem) return resolveSceneEvidence(deck, sceneId, sceneFocusItem.source);
  }

  return null;
}

export function resolveScenePresentation(deck: SceneDeckViewModel, state: SceneInteractionState): ScenePresentation {
  const activeScene = deck.scenes.find((scene) => scene.id === state.activeSceneId) ?? deck.scenes[0];
  if (!activeScene) {
    throw new Error("Cannot resolve scene presentation for an empty scene deck");
  }
  const activeFocusSource =
    state.activeFocusSourceByScene[activeScene.id] ?? activeScene.focusItems[0]?.source ?? activeScene.tasks[0]?.source;
  return {
    activeScene,
    activeFocusSource,
    activeEvidence: activeFocusSource ? resolveSceneEvidence(deck, activeScene.id, activeFocusSource) ?? undefined : undefined,
    taskStateByTaskId: state.taskStateByTaskId,
  };
}
