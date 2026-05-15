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
  const slot = bindingSlot ?? resolveSlotForSource(topic, context.source);
  if (!slot) return null;

  if (binding) {
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
    };
  }

  const copy = derivedCopy(topic, context.source, context.selectedIds ?? [], locale);
  if (!copy) return null;

  return {
    source: context.source,
    sourceId: sourceId(context.source),
    visualSlotId: slot.id,
    status: context.result ?? "selected",
    ...copy,
    bindingQuality: "derived",
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
