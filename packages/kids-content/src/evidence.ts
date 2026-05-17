import type {
  ClickTask,
  EvidenceCoverageReport,
  EvidenceResolveContext,
  EvidenceSourcePath,
  EvidenceStatus,
  Locale,
  Topic,
  VisualEvidenceBinding,
  VisualEvidenceState,
  VisualFocus,
  VisualSlot,
} from "../../../boards/kids-world/src/types/topic";

type CoverageBucket = {
  total: number;
  resolved: number;
};

const defaultLocale: Locale = "zh-CN";

function sourceId(source: EvidenceSourcePath): string {
  const parts = source.split(".");
  return parts[parts.length - 1] ?? source;
}

function sourceKind(source: EvidenceSourcePath): string {
  if (source.startsWith("mechanism.steps.")) return "mechanism.steps";
  if (source.startsWith("secondaryMechanism.steps.")) return "secondaryMechanism.steps";
  if (source.includes(".options.")) return "clickTasks.options";
  return source.split(".")[0] ?? source;
}

function taskIdFromOptionSource(source: EvidenceSourcePath): string | null {
  const match = source.match(/^clickTasks\.([^.]+)\.options\./);
  return match?.[1] ?? null;
}

function optionIdFromSource(source: EvidenceSourcePath): string {
  const parts = source.split(".");
  return parts[parts.length - 1] ?? source;
}

function parentSource(source: EvidenceSourcePath): EvidenceSourcePath | null {
  const taskId = taskIdFromOptionSource(source);
  return taskId ? (`clickTasks.${taskId}` as EvidenceSourcePath) : null;
}

function findSlotById(topic: Topic, id: string): VisualSlot | null {
  return topic.visualSlots?.find((slot) => slot.id === id) ?? null;
}

function firstSlot(topic: Topic, predicates: Array<(slot: VisualSlot) => boolean>): VisualSlot | null {
  const slots = topic.visualSlots ?? [];
  for (const predicate of predicates) {
    const slot = slots.find(predicate);
    if (slot) return slot;
  }
  return null;
}

function resolveSlotForSource(topic: Topic, source: EvidenceSourcePath): VisualSlot | null {
  const id = sourceId(source);

  if (source.startsWith("classificationGroups.")) {
    return firstSlot(topic, [
      (slot) => slot.target === `classificationGroups.${id}`,
      (slot) => slot.target === "classificationGroups",
      (slot) => slot.target === "representativeObjects",
      (slot) => slot.target === "hero",
    ]);
  }

  if (source.startsWith("representativeObjects.")) {
    return firstSlot(topic, [
      (slot) => slot.target === `representativeObjects.${id}`,
      (slot) => slot.role === "observation" && slot.target === "representativeObjects",
      (slot) => slot.target === "representativeObjects",
      (slot) => slot.target === "hero",
    ]);
  }

  if (source.startsWith("mechanism.steps.")) {
    return firstSlot(topic, [
      (slot) => slot.target === `mechanism.${id}`,
      (slot) => slot.target === "mechanism",
      (slot) => slot.role === "process",
      (slot) => slot.target === "clickTasks",
      (slot) => slot.target === "hero",
    ]);
  }

  if (source.startsWith("secondaryMechanism.steps.")) {
    return firstSlot(topic, [
      (slot) => slot.target === `secondaryMechanism.${id}`,
      (slot) => slot.target === "secondaryMechanism",
      (slot) => slot.target === "mechanism",
      (slot) => slot.role === "process",
      (slot) => slot.target === "hero",
    ]);
  }

  if (source.startsWith("comparePairs.")) {
    return firstSlot(topic, [
      (slot) => slot.target === `comparePairs.${id}`,
      (slot) => slot.target === "comparePairs",
      (slot) => slot.role === "compare",
      (slot) => slot.target === "hero",
    ]);
  }

  if (source.startsWith("clickTasks.")) {
    const taskId = taskIdFromOptionSource(source) ?? id;
    return firstSlot(topic, [
      (slot) => slot.target === `clickTasks.${taskId}`,
      (slot) => slot.target === "clickTasks",
      (slot) => slot.role === "task",
      (slot) => slot.target === "hero",
    ]);
  }

  return firstSlot(topic, [(slot) => slot.target === "hero"]);
}

function findBinding(topic: Topic, source: EvidenceSourcePath): VisualEvidenceBinding | null {
  const exact = topic.visualEvidenceBindings?.find((binding) => binding.source === source);
  if (exact) return exact;
  const parent = parentSource(source);
  return parent ? topic.visualEvidenceBindings?.find((binding) => binding.source === parent) ?? null : null;
}

function taskForOptionSource(topic: Topic, source: EvidenceSourcePath): ClickTask | null {
  const taskId = taskIdFromOptionSource(source);
  return taskId ? topic.clickTasks.find((task) => task.id === taskId) ?? null : null;
}

function representativeObjectIds(topic: Topic): Set<string> {
  return new Set(topic.representativeObjects.map((object) => object.id));
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

function taskResultForOption(task: ClickTask, optionId: string, selectedIds: string[] = []): EvidenceStatus {
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

function deriveFocusForSource(topic: Topic, source: EvidenceSourcePath, selectedIds: string[] = []): VisualFocus | undefined {
  const id = sourceId(source);

  if (source.startsWith("mechanism.steps.")) {
    const index = topic.mechanism.steps.findIndex((item) => item.id === id);
    return {
      mode: "path-step",
      activeRegionIds: [id],
      progress: index >= 0 ? { current: index + 1, total: topic.mechanism.steps.length } : undefined,
    };
  }

  if (source.startsWith("secondaryMechanism.steps.")) {
    const steps = topic.secondaryMechanism?.steps ?? [];
    const index = steps.findIndex((item) => item.id === id);
    return {
      mode: "path-step",
      activeRegionIds: [id],
      progress: index >= 0 ? { current: index + 1, total: steps.length } : undefined,
    };
  }

  if (source.startsWith("classificationGroups.")) {
    return {
      mode: "group",
      activeRegionIds: topic.representativeObjects
        .filter((object) => object.groupId === id)
        .map((object) => object.id),
      dimOthers: true,
    };
  }

  if (source.startsWith("representativeObjects.")) {
    return {
      mode: "hotspot",
      activeRegionIds: [id],
      dimOthers: true,
    };
  }

  if (source.startsWith("comparePairs.")) {
    return {
      mode: "whole-image",
      activeRegionIds: [id],
    };
  }

  if (source.startsWith("clickTasks.")) {
    const taskId = taskIdFromOptionSource(source);
    const task = taskId ? topic.clickTasks.find((item) => item.id === taskId) : topic.clickTasks.find((item) => item.id === id);
    if (task?.type === "sequenceClick") {
      return {
        mode: "sequence-progress",
        activeRegionIds: selectedIds.length > 0 ? selectedIds : [id],
        progress: selectedIds.length > 0 ? { current: selectedIds.length, total: task.correctSequence?.length ?? selectedIds.length } : undefined,
      };
    }

    return {
      mode: "hotspot",
      activeRegionIds: [id],
      dimOthers: true,
    };
  }

  return {
    mode: "whole-image",
    activeRegionIds: [id],
  };
}

function gridRegions(
  ids: string[],
  labelForId: (id: string) => string | undefined,
  options: { columns?: number; top?: number; left?: number; width?: number; height?: number } = {},
): NonNullable<VisualFocus["regions"]> {
  const columns = options.columns ?? (ids.length <= 4 ? 2 : ids.length <= 6 ? 3 : 4);
  const rows = Math.max(1, Math.ceil(ids.length / columns));
  const left = options.left ?? 0.06;
  const top = options.top ?? 0.1;
  const totalWidth = options.width ?? 0.88;
  const totalHeight = options.height ?? 0.72;
  const cellWidth = totalWidth / columns;
  const cellHeight = totalHeight / rows;
  return ids.map((id, index) => {
    const column = index % columns;
    const row = Math.floor(index / columns);
    return {
      id,
      label: labelForId(id),
      x: left + column * cellWidth + cellWidth * 0.08,
      y: top + row * cellHeight + cellHeight * 0.08,
      width: cellWidth * 0.84,
      height: cellHeight * 0.84,
    };
  });
}

function objectRegions(topic: Topic): NonNullable<VisualFocus["regions"]> {
  return gridRegions(
    topic.representativeObjects.map((object) => object.id),
    (id) => topic.representativeObjects.find((object) => object.id === id)?.name,
  );
}

function taskOptionRegions(task: ClickTask): NonNullable<VisualFocus["regions"]> {
  const options = taskOptions(task);
  return gridRegions(options.map((option) => option.id), (id) => options.find((option) => option.id === id)?.label, {
    columns: options.length <= 4 ? 2 : 3,
    top: 0.14,
    height: 0.66,
  });
}

function mechanismRegions(topic: Topic, source: EvidenceSourcePath): NonNullable<VisualFocus["regions"]> {
  const steps = source.startsWith("secondaryMechanism.steps.") ? topic.secondaryMechanism?.steps ?? [] : topic.mechanism.steps;
  return gridRegions(steps.map((step) => step.id), (id) => steps.find((step) => step.id === id)?.shortTitle, {
    columns: steps.length,
    top: 0.22,
    left: 0.05,
    width: 0.9,
    height: 0.46,
  });
}

function compareRegions(): NonNullable<VisualFocus["regions"]> {
  return [
    { id: "left", label: "A", x: 0.08, y: 0.2, width: 0.36, height: 0.6 },
    { id: "right", label: "B", x: 0.56, y: 0.2, width: 0.36, height: 0.6 },
  ];
}

function withFocusRegions(topic: Topic, source: EvidenceSourcePath, focus: VisualFocus | undefined, selectedIds: string[] = []): VisualFocus | undefined {
  if (!focus) return focus;
  if (focus.regions?.length) return focus;

  if (source.startsWith("classificationGroups.") || source.startsWith("representativeObjects.")) {
    return { ...focus, regions: objectRegions(topic) };
  }

  if (source.startsWith("mechanism.steps.") || source.startsWith("secondaryMechanism.steps.")) {
    return { ...focus, regions: mechanismRegions(topic, source) };
  }

  if (source.startsWith("comparePairs.")) {
    const activeRegionIds = focus.activeRegionIds?.some((id) => id === "left" || id === "right")
      ? focus.activeRegionIds
      : ["left", "right"];
    return { ...focus, mode: "group", regions: compareRegions(), activeRegionIds };
  }

  if (source.startsWith("clickTasks.")) {
    const task = taskForOptionSource(topic, source);
    if (!task) return focus;
    const optionId = optionIdFromSource(source);
    const objectIds = representativeObjectIds(topic);
    if (task.type === "findTarget" && objectIds.has(optionId)) {
      return {
        ...focus,
        mode: "hotspot",
        regions: objectRegions(topic),
        activeRegionIds: [optionId],
      };
    }
    return {
      ...focus,
      regions: taskOptionRegions(task),
      activeRegionIds: selectedIds.length > 0 ? selectedIds : focus.activeRegionIds,
    };
  }

  return focus;
}

function preferredBindingSlot(topic: Topic, source: EvidenceSourcePath, bindingSlot: VisualSlot | null): VisualSlot | null {
  if (!source.includes(".options.")) return bindingSlot;
  const task = taskForOptionSource(topic, source);
  if (task?.type !== "findTarget") return bindingSlot;
  const taskSlot = firstSlot(topic, [(slot) => slot.target === `clickTasks.${task.id}`]);
  if (taskSlot) return taskSlot;
  const optionId = optionIdFromSource(source);
  if (representativeObjectIds(topic).has(optionId)) {
    return firstSlot(topic, [
      (slot) => slot.role === "observation" && slot.target === "representativeObjects",
      (slot) => slot.target === "representativeObjects",
    ]) ?? bindingSlot;
  }
  return bindingSlot;
}

function derivedCopy(topic: Topic, source: EvidenceSourcePath, selectedIds: string[], locale: Locale) {
  const id = sourceId(source);

  if (source.startsWith("classificationGroups.")) {
    const group = topic.classificationGroups.find((item) => item.id === id);
    if (!group) return null;
    const objectNames = topic.representativeObjects
      .filter((object) => object.groupId === group.id)
      .map((object) => object.name);
    return {
      evidenceTitle: group.name,
      observePrompt: locale === "zh-CN" ? "看一看哪些对象属于这一类。" : "Look for objects that belong to this group.",
      evidenceCopy: objectNames.length ? `${group.childExplanation} ${objectNames.join("、")} 都可以放进这一类。` : group.childExplanation,
      selectedLabels: objectNames,
    };
  }

  if (source.startsWith("representativeObjects.")) {
    const object = topic.representativeObjects.find((item) => item.id === id);
    if (!object) return null;
    return {
      evidenceTitle: object.name,
      observePrompt: object.visualHint,
      evidenceCopy: object.childExplanation,
      selectedLabels: [object.name],
    };
  }

  if (source.startsWith("mechanism.steps.")) {
    const index = topic.mechanism.steps.findIndex((item) => item.id === id);
    const step = topic.mechanism.steps[index];
    if (!step) return null;
    return {
      evidenceTitle: step.shortTitle,
      observePrompt: locale === "zh-CN" ? `当前第 ${index + 1} 步。` : `Current step ${index + 1}.`,
      evidenceCopy: step.childExplanation,
      selectedLabels: [step.shortTitle],
    };
  }

  if (source.startsWith("secondaryMechanism.steps.")) {
    const steps = topic.secondaryMechanism?.steps ?? [];
    const index = steps.findIndex((item) => item.id === id);
    const step = steps[index];
    if (!step) return null;
    return {
      evidenceTitle: step.shortTitle,
      observePrompt: locale === "zh-CN" ? `当前第 ${index + 1} 步。` : `Current step ${index + 1}.`,
      evidenceCopy: step.childExplanation,
      selectedLabels: [step.shortTitle],
    };
  }

  if (source.startsWith("comparePairs.")) {
    const pair = topic.comparePairs.find((item) => item.id === id);
    if (!pair) return null;
    return {
      evidenceTitle: pair.title,
      observePrompt: locale === "zh-CN" ? `比较 ${pair.a.name} 和 ${pair.b.name} 的线索。` : `Compare clues for ${pair.a.name} and ${pair.b.name}.`,
      evidenceCopy: `${pair.a.name}: ${pair.a.points.join("；")}。${pair.b.name}: ${pair.b.points.join("；")}。${pair.childConclusion}`,
      selectedLabels: [pair.a.name, pair.b.name],
    };
  }

  if (source.startsWith("clickTasks.")) {
    const taskId = taskIdFromOptionSource(source) ?? id;
    const task = topic.clickTasks.find((item) => item.id === taskId);
    if (!task) return null;
    const optionId = taskIdFromOptionSource(source) ? id : selectedIds[0];
    const option = optionId ? taskOptions(task).find((item) => item.id === optionId) : null;
    const isCorrect = optionId ? taskResultForOption(task, optionId, selectedIds) : "selected";
    const wrongHint = optionId && task.wrongHints?.[optionId] ? task.wrongHints[optionId] : task.wrongHint;
    const evidenceCopy =
      isCorrect === "wrong"
        ? wrongHint ?? task.prompt ?? task.title
        : isCorrect === "complete" || isCorrect === "correct"
          ? task.successCopy ?? task.prompt ?? task.title
          : task.prompt ?? task.title;
    return {
      evidenceTitle: option ? option.label : task.title,
      observePrompt: task.prompt,
      evidenceCopy,
      selectedLabels: option ? [option.label] : selectedIds,
    };
  }

  return null;
}

export function resolveVisualEvidence(topic: Topic, context: EvidenceResolveContext): VisualEvidenceState | null {
  const locale = context.locale ?? defaultLocale;
  const binding = findBinding(topic, context.source);
  const bindingSlot = binding ? findSlotById(topic, binding.visualSlotId) : null;
  const slot = preferredBindingSlot(topic, context.source, bindingSlot) ?? resolveSlotForSource(topic, context.source);
  if (!slot) return null;
  const selectedIds = context.selectedIds ?? [];

  if (binding) {
    const focus = withFocusRegions(topic, context.source, binding.focus ?? deriveFocusForSource(topic, context.source, selectedIds), selectedIds);
    return {
      source: context.source,
      sourceId: sourceId(context.source),
      visualSlotId: slot.id,
      status: context.result ?? binding.expectedStatus ?? "selected",
      evidenceTitle: binding.evidenceTitle,
      observePrompt: binding.observePrompt,
      evidenceCopy: binding.evidenceCopy,
      selectedLabels: context.selectedIds,
      markerChips: binding.markerChips,
      bindingQuality: "explicit",
      nextPrompt: binding.nextPrompt,
      focus,
    };
  }

  const copy = derivedCopy(topic, context.source, selectedIds, locale);
  if (!copy) return null;
  const focus = withFocusRegions(topic, context.source, deriveFocusForSource(topic, context.source, selectedIds), selectedIds);

  return {
    source: context.source,
    sourceId: sourceId(context.source),
    visualSlotId: slot.id,
    status: context.result ?? "selected",
    ...copy,
    bindingQuality: "derived",
    focus,
  };
}

function allOptionSources(task: ClickTask): EvidenceSourcePath[] {
  return taskOptions(task).map((option) => `clickTasks.${task.id}.options.${option.id}` as EvidenceSourcePath);
}

function sourceList(topic: Topic): EvidenceSourcePath[] {
  return [
    ...topic.classificationGroups.map((item) => `classificationGroups.${item.id}` as EvidenceSourcePath),
    ...topic.representativeObjects.map((item) => `representativeObjects.${item.id}` as EvidenceSourcePath),
    ...topic.mechanism.steps.map((item) => `mechanism.steps.${item.id}` as EvidenceSourcePath),
    ...(topic.secondaryMechanism?.steps ?? []).map((item) => `secondaryMechanism.steps.${item.id}` as EvidenceSourcePath),
    ...topic.comparePairs.map((item) => `comparePairs.${item.id}` as EvidenceSourcePath),
    ...topic.clickTasks.flatMap(allOptionSources),
  ];
}

function bucketCoverage(topic: Topic, sources: EvidenceSourcePath[]): CoverageBucket {
  const resolved = sources.filter((source) => resolveVisualEvidence(topic, { source }) !== null).length;
  return { total: sources.length, resolved };
}

function ratio(bucket: CoverageBucket): number {
  return bucket.total === 0 ? 1 : bucket.resolved / bucket.total;
}

export function getTopicEvidenceCoverage(topic: Topic): EvidenceCoverageReport {
  const sources = sourceList(topic);
  const resolved = sources
    .map((source) => ({ source, evidence: resolveVisualEvidence(topic, { source }) }))
    .filter((item) => item.evidence);
  const unresolvedSources = sources.filter((source) => !resolved.some((item) => item.source === source));
  const explicitBindingCount = resolved.filter((item) => item.evidence?.bindingQuality === "explicit").length;
  const derivedBindingCount = resolved.filter((item) => item.evidence?.bindingQuality === "derived").length;

  const clickTaskBucket = bucketCoverage(topic, topic.clickTasks.flatMap(allOptionSources));
  const mechanismSources = [
    ...topic.mechanism.steps.map((item) => `mechanism.steps.${item.id}` as EvidenceSourcePath),
    ...(topic.secondaryMechanism?.steps ?? []).map((item) => `secondaryMechanism.steps.${item.id}` as EvidenceSourcePath),
  ];
  const mechanismBucket = bucketCoverage(topic, mechanismSources);
  const compareBucket = bucketCoverage(topic, topic.comparePairs.map((item) => `comparePairs.${item.id}` as EvidenceSourcePath));
  const objectBucket = bucketCoverage(topic, topic.representativeObjects.map((item) => `representativeObjects.${item.id}` as EvidenceSourcePath));
  const derivedFallbackRatio = sources.length === 0 ? 0 : derivedBindingCount / sources.length;

  return {
    slug: topic.slug,
    totalInteractiveSources: sources.length,
    resolvedEvidenceSources: resolved.length,
    unresolvedSources,
    explicitBindingCount,
    derivedBindingCount,
    clickTaskOptionCoverage: ratio(clickTaskBucket),
    mechanismStepCoverage: ratio(mechanismBucket),
    comparePairCoverage: ratio(compareBucket),
    representativeObjectCoverage: ratio(objectBucket),
    derivedFallbackRatio,
    pass: unresolvedSources.length === 0 && derivedFallbackRatio <= 0.6,
  };
}
