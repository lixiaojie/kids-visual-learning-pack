import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const errors = [];

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(root, relativePath), "utf8"));
}

function optionIds(task) {
  return task.options?.map((option) => option.id) ?? [...(task.targetIds ?? []), ...(task.decoyIds ?? [])];
}

function interactiveSources(topic) {
  return [
    ...(topic.classificationGroups ?? []).map((item) => `classificationGroups.${item.id}`),
    ...(topic.representativeObjects ?? []).map((item) => `representativeObjects.${item.id}`),
    ...(topic.mechanism?.steps ?? []).map((item) => `mechanism.steps.${item.id}`),
    ...(topic.secondaryMechanism?.steps ?? []).map((item) => `secondaryMechanism.steps.${item.id}`),
    ...(topic.comparePairs ?? []).map((item) => `comparePairs.${item.id}`),
    ...(topic.clickTasks ?? []).flatMap((task) => optionIds(task).map((optionId) => `clickTasks.${task.id}.options.${optionId}`)),
  ];
}

function sourceId(source) {
  const parts = source.split(".");
  return parts[parts.length - 1] ?? source;
}

function focusKey(binding, source) {
  const focus = binding?.focus;
  const active = focus?.activeRegionIds?.length ? focus.activeRegionIds.join("|") : sourceId(source);
  return `${focus?.mode ?? "derived"}:${active}`;
}

const evidenceSource = fs.readFileSync(path.join(root, "packages/kids-content/src/evidence.ts"), "utf8");
if (!evidenceSource.includes("deriveFocusForSource") || !evidenceSource.includes("focus:")) {
  errors.push("packages/kids-content/src/evidence.ts must return explicit or derived focus for evidence");
}

const registry = readJson("boards/kids-world/src/data/topic-registry.json");
const renderReadySlugs = registry.topics
  .filter((topic) => topic.status === "render-ready" || topic.contentStatus === "render-ready")
  .map((topic) => topic.slug);

for (const slug of renderReadySlugs) {
  const topic = readJson(`boards/kids-world/src/data/topics/${slug}.json`);
  const bindings = new Map((topic.visualEvidenceBindings ?? []).map((binding) => [binding.source, binding]));
  const slotUse = new Map();

  for (const source of interactiveSources(topic)) {
    const binding = bindings.get(source);
    const slotId = binding?.visualSlotId ?? "derived";
    const list = slotUse.get(slotId) ?? [];
    list.push({ source, key: focusKey(binding, source) });
    slotUse.set(slotId, list);
  }

  for (const [slotId, list] of slotUse) {
    if (slotId === "derived" || list.length < 2) continue;
    const focusKeys = new Set(list.map((item) => item.key));
    if (focusKeys.size === 1) {
      errors.push(`${slug} visualSlotId ${slotId} is shared by ${list.length} sources without distinguishable focus`);
    }
  }
}

if (errors.length > 0) {
  console.error(errors.join("\n"));
  process.exit(1);
}

console.log(`Evidence focus checked for ${renderReadySlugs.length} render-ready topics`);
