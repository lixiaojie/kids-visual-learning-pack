import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const registry = readJson("boards/kids-world/src/data/topic-registry.json");
const manifest = readJson("boards/kids-world/src/data/image-generation-manifest.json");
const manifestAssetIds = new Set((manifest.assets || []).map((asset) => asset.assetId));
const errors = [];
const warnings = [];

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(root, relativePath), "utf8"));
}

function optionIds(task) {
  return task.options?.map((option) => option.id) ?? [...(task.targetIds ?? []), ...(task.decoyIds ?? [])];
}

function includesCjk(value) {
  return /[\u3400-\u9fff]/.test(String(value ?? ""));
}

function bindingText(binding) {
  return [
    binding.evidenceTitle,
    binding.observePrompt,
    binding.evidenceCopy,
    ...(binding.markerChips ?? []).flatMap((chip) => [chip.label, chip.meaning]),
    binding.nextPrompt,
  ]
    .filter(Boolean)
    .join("\n");
}

function sourcesForTopic(topic) {
  return [
    ...topic.classificationGroups.map((item) => `classificationGroups.${item.id}`),
    ...topic.representativeObjects.map((item) => `representativeObjects.${item.id}`),
    ...topic.mechanism.steps.map((item) => `mechanism.steps.${item.id}`),
    ...(topic.secondaryMechanism?.steps ?? []).map((item) => `secondaryMechanism.steps.${item.id}`),
    ...topic.comparePairs.map((item) => `comparePairs.${item.id}`),
    ...topic.clickTasks.flatMap((task) => optionIds(task).map((optionId) => `clickTasks.${task.id}.options.${optionId}`)),
  ];
}

function firstSlot(topic, predicates) {
  const slots = topic.visualSlots ?? [];
  for (const predicate of predicates) {
    const slot = slots.find(predicate);
    if (slot) return slot;
  }
  return null;
}

function derivedSlot(topic, source) {
  const parts = source.split(".");
  const id = parts.at(-1);
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
      (slot) => slot.target === "representativeObjects",
      (slot) => slot.role === "observation",
      (slot) => slot.target === "hero",
    ]);
  }
  if (source.startsWith("mechanism.steps.")) {
    return firstSlot(topic, [
      (slot) => slot.target === `mechanism.${id}`,
      (slot) => slot.target === "mechanism",
      (slot) => slot.role === "process",
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
    const taskId = parts[1];
    return firstSlot(topic, [
      (slot) => slot.target === `clickTasks.${taskId}`,
      (slot) => slot.target === "clickTasks",
      (slot) => slot.role === "task",
      (slot) => slot.target === "hero",
    ]);
  }
  return firstSlot(topic, [(slot) => slot.target === "hero"]);
}

function coverageRatio(topic, sources, resolvedSources) {
  if (sources.length === 0) return 1;
  return sources.filter((source) => resolvedSources.has(source)).length / sources.length;
}

function reportForTopic(topic) {
  const bindings = topic.visualEvidenceBindings ?? [];
  const bindingBySource = new Map(bindings.map((binding) => [binding.source, binding]));
  const slotsById = new Map((topic.visualSlots ?? []).map((slot) => [slot.id, slot]));
  const sources = sourcesForTopic(topic);
  const resolvedSources = new Set();
  let explicit = 0;
  let derived = 0;

  for (const slot of topic.visualSlots ?? []) {
    if (!manifestAssetIds.has(slot.assetId)) {
      errors.push(`${topic.slug}: visualSlot "${slot.id}" references missing assetId "${slot.assetId}"`);
    }
  }

  for (const pair of topic.comparePairs ?? []) {
    if (!pair.a?.points?.length || !pair.b?.points?.length) {
      errors.push(`${topic.slug}: comparePair "${pair.id}" must include a.points and b.points`);
    }
  }

  for (const task of topic.clickTasks ?? []) {
    if (task.type !== "sequenceClick") continue;
    const sequence = task.correctSequence ?? [];
    for (const optionId of sequence.slice(1)) {
      const binding = bindingBySource.get(`clickTasks.${task.id}.options.${optionId}`);
      if (binding?.expectedStatus === "wrong") {
        errors.push(`${topic.slug}: sequenceClick "${task.id}" correct step "${optionId}" must not have wrong expectedStatus`);
      }
      const wrongHint = task.wrongHints?.[optionId] ?? task.wrongHint;
      if (binding && wrongHint && binding.evidenceCopy === wrongHint) {
        errors.push(`${topic.slug}: sequenceClick "${task.id}" correct step "${optionId}" must not reuse wrongHint as evidenceCopy`);
      }
    }
  }

  const enOverlay = readJson(`boards/kids-world/src/data/locales/en-US/topics/${topic.slug}.json`);
  const enBindingsById = new Map((enOverlay.visualEvidenceBindings ?? []).map((binding) => [binding.id, binding]));
  for (const binding of bindings) {
    const enBinding = enBindingsById.get(binding.id);
    if (!enBinding) {
      errors.push(`${topic.slug}: en-US visualEvidenceBinding "${binding.id}" is missing`);
      continue;
    }
  }
  for (const binding of enOverlay.visualEvidenceBindings ?? []) {
    if (includesCjk(bindingText(binding))) {
      errors.push(`${topic.slug}: en-US visualEvidenceBinding "${binding.id}" contains CJK text`);
    }
  }

  const unresolvedSources = [];
  for (const source of sources) {
    const binding = bindingBySource.get(source);
    if (binding) {
      if (!slotsById.has(binding.visualSlotId)) {
        errors.push(`${topic.slug}: binding "${binding.id}" references missing visualSlotId "${binding.visualSlotId}"`);
        unresolvedSources.push(source);
        continue;
      }
      explicit += 1;
      resolvedSources.add(source);
      continue;
    }

    const slot = derivedSlot(topic, source);
    if (slot) {
      derived += 1;
      resolvedSources.add(source);
      continue;
    }
    unresolvedSources.push(source);
  }

  const clickTaskSources = topic.clickTasks.flatMap((task) => optionIds(task).map((optionId) => `clickTasks.${task.id}.options.${optionId}`));
  const mechanismSources = [
    ...topic.mechanism.steps.map((item) => `mechanism.steps.${item.id}`),
    ...(topic.secondaryMechanism?.steps ?? []).map((item) => `secondaryMechanism.steps.${item.id}`),
  ];
  const compareSources = topic.comparePairs.map((item) => `comparePairs.${item.id}`);
  const objectSources = topic.representativeObjects.map((item) => `representativeObjects.${item.id}`);
  const derivedFallbackRatio = sources.length === 0 ? 0 : derived / sources.length;

  if (derivedFallbackRatio > 0.4) {
    warnings.push(`${topic.slug}: derived fallback ratio ${Math.round(derivedFallbackRatio * 100)}% exceeds P0 refinement target`);
  }
  if (derivedFallbackRatio > 0.6) {
    errors.push(`${topic.slug}: derived fallback ratio ${Math.round(derivedFallbackRatio * 100)}% exceeds failure threshold`);
  }
  if (unresolvedSources.length > 0) {
    errors.push(`${topic.slug}: unresolved evidence sources: ${unresolvedSources.join(", ")}`);
  }

  return {
    slug: topic.slug,
    totalInteractiveSources: sources.length,
    resolvedEvidenceSources: resolvedSources.size,
    unresolvedSources,
    explicitBindingCount: explicit,
    derivedBindingCount: derived,
    clickTaskOptionCoverage: coverageRatio(topic, clickTaskSources, resolvedSources),
    mechanismStepCoverage: coverageRatio(topic, mechanismSources, resolvedSources),
    comparePairCoverage: coverageRatio(topic, compareSources, resolvedSources),
    representativeObjectCoverage: coverageRatio(topic, objectSources, resolvedSources),
    pass: unresolvedSources.length === 0 && derivedFallbackRatio <= 0.6,
  };
}

const renderReadySlugs = registry.topics
  .filter((topic) => topic.status === "render-ready" || topic.contentStatus === "render-ready")
  .map((topic) => topic.slug);
const reports = renderReadySlugs.map((slug) => reportForTopic(readJson(`boards/kids-world/src/data/topics/${slug}.json`)));

console.log("Evidence coverage summary");
for (const report of reports) {
  console.log(
    `- ${report.slug}: ${report.pass ? "pass" : "fail"}, ${report.resolvedEvidenceSources}/${report.totalInteractiveSources} sources resolved, explicit=${report.explicitBindingCount}, derived=${report.derivedBindingCount}`,
  );
}

for (const warning of warnings) {
  console.warn(`warning: ${warning}`);
}

if (errors.length > 0) {
  console.error("evidence coverage validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}
