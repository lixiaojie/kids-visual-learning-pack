import { readFileSync } from "node:fs";
import { strict as assert } from "node:assert";

const root = new URL("./", import.meta.url);
const readJson = (path) => JSON.parse(readFileSync(new URL(path, root), "utf8"));

const registry = readJson("./src/data/topic-registry.json");
const renderReadySlugs = registry.topics
  .filter((topic) => topic.status === "render-ready" || topic.contentStatus === "render-ready")
  .map((topic) => topic.slug);

function optionSources(task) {
  const optionIds =
    task.options?.map((option) => option.id) ??
    [...(task.targetIds ?? []), ...(task.decoyIds ?? [])];
  return optionIds.map((optionId) => `clickTasks.${task.id}.options.${optionId}`);
}

for (const slug of renderReadySlugs) {
  const topic = readJson(`./src/data/topics/${slug}.json`);
  const bindingSources = new Set((topic.visualEvidenceBindings ?? []).map((binding) => binding.source));
  const slotIds = new Set((topic.visualSlots ?? []).map((slot) => slot.id));

  assert.ok(Array.isArray(topic.visualEvidenceBindings), `${slug} should define visualEvidenceBindings`);

  for (const source of topic.classificationGroups.map((item) => `classificationGroups.${item.id}`)) {
    assert.ok(bindingSources.has(source), `${slug} missing evidence binding for ${source}`);
  }

  for (const source of topic.representativeObjects.map((item) => `representativeObjects.${item.id}`)) {
    assert.ok(bindingSources.has(source), `${slug} missing evidence binding for ${source}`);
  }

  for (const source of topic.mechanism.steps.map((item) => `mechanism.steps.${item.id}`)) {
    assert.ok(bindingSources.has(source), `${slug} missing evidence binding for ${source}`);
  }

  for (const source of topic.secondaryMechanism?.steps?.map((item) => `secondaryMechanism.steps.${item.id}`) ?? []) {
    assert.ok(bindingSources.has(source), `${slug} missing evidence binding for ${source}`);
  }

  for (const source of topic.comparePairs.map((item) => `comparePairs.${item.id}`)) {
    assert.ok(bindingSources.has(source), `${slug} missing evidence binding for ${source}`);
  }

  for (const task of topic.clickTasks) {
    for (const source of optionSources(task)) {
      assert.ok(bindingSources.has(source), `${slug} missing evidence binding for ${source}`);
    }
  }

  for (const binding of topic.visualEvidenceBindings) {
    assert.ok(slotIds.has(binding.visualSlotId), `${slug} binding ${binding.id} uses missing visualSlotId ${binding.visualSlotId}`);
  }
}

console.log(`Evidence binding structure checked for ${renderReadySlugs.length} render-ready topics`);
