import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const errors = [];

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(root, relativePath), "utf8"));
}

function assertSource(topic, source, label) {
  if (!source) {
    errors.push(`${topic.slug} missing default evidence source for ${label}`);
    return;
  }

  const slotIds = new Set((topic.visualSlots ?? []).map((slot) => slot.id));
  const binding = (topic.visualEvidenceBindings ?? []).find((item) => item.source === source);
  if (binding && !slotIds.has(binding.visualSlotId)) {
    errors.push(`${topic.slug} source ${source} points to missing visualSlotId ${binding.visualSlotId}`);
  }
}

function expectedStageSources(topic) {
  return [
    topic.classificationGroups?.[0] ? ["classify", `classificationGroups.${topic.classificationGroups[0].id}`] : null,
    topic.representativeObjects?.[0] ? ["inspect", `representativeObjects.${topic.representativeObjects[0].id}`] : null,
    topic.mechanism?.steps?.[0] ? ["trace", `mechanism.steps.${topic.mechanism.steps[0].id}`] : null,
    topic.comparePairs?.[0] ? ["compare", `comparePairs.${topic.comparePairs[0].id}`] : null,
    topic.clickTasks?.[0] ? ["tasks", `clickTasks.${topic.clickTasks[0].id}`] : null,
  ].filter(Boolean);
}

const packageIndex = fs.readFileSync(path.join(root, "packages/kids-content/src/index.ts"), "utf8");
const visualSlotsSource = fs.readFileSync(path.join(root, "packages/kids-content/src/visual-slots.ts"), "utf8");

if (!fs.existsSync(path.join(root, "packages/kids-content/src/interaction.ts"))) {
  errors.push("packages/kids-content/src/interaction.ts must define the shared topic interaction state machine");
}
if (!packageIndex.includes("createInitialTopicInteractionState") || !packageIndex.includes("resolveTopicPresentation")) {
  errors.push("packages/kids-content/src/index.ts must export the shared interaction helpers");
}
if (!visualSlotsSource.includes("getDefaultEvidenceSourceForStage") || !visualSlotsSource.includes("defaultEvidenceSource")) {
  errors.push("packages/kids-content/src/visual-slots.ts must provide defaultEvidenceSource for learning flow stages");
}

const registry = readJson("boards/kids-world/src/data/topic-registry.json");
const renderReadySlugs = registry.topics
  .filter((topic) => topic.status === "render-ready" || topic.contentStatus === "render-ready")
  .map((topic) => topic.slug);

for (const slug of renderReadySlugs) {
  const topic = readJson(`boards/kids-world/src/data/topics/${slug}.json`);
  for (const [stageId, source] of expectedStageSources(topic)) {
    assertSource(topic, source, stageId);
  }
}

if (errors.length > 0) {
  console.error(errors.join("\n"));
  process.exit(1);
}

console.log(`Interaction flow defaults checked for ${renderReadySlugs.length} render-ready topics`);
