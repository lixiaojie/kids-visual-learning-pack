import assert from "node:assert/strict";
import { getTopic, materializeVisualEvidenceFocus, normalizeTopicInteraction } from "../packages/kids-content/src/index";

const topic = getTopic("cicada-life", "zh-CN");
assert.ok(topic, "cicada-life topic should exist");

const viewModel = normalizeTopicInteraction(topic, {
  locale: "zh-CN",
  mode: "dev",
  platform: "web",
});

assert.equal(viewModel.topicId, "cicada-life");
assert.equal(viewModel.locale, "zh-CN");
assert.ok(viewModel.stages.length >= 6, "view model should expose the current learning flow stages");
assert.equal(viewModel.initialState.activeStageId, viewModel.stages[0]?.id);
assert.deepEqual(
  viewModel.stages.map((stage) => ({
    id: stage.id,
    quality: stage.quality,
    label: stage.label,
    blocks: stage.blocks.map((block) => block.kind),
  })),
  [
    { id: "observe", quality: "authored", label: "真实发现", blocks: ["hero"] },
    { id: "classify", quality: "authored", label: "认出若虫", blocks: ["classification", "classification", "classification"] },
    { id: "inspect", quality: "authored", label: "生命周期", blocks: ["objects", "objects", "objects"] },
    { id: "trace", quality: "authored", label: "羽化过程", blocks: ["mechanism", "mechanism"] },
    { id: "compare", quality: "authored", label: "易混比较", blocks: ["compare", "compare", "compare"] },
    { id: "tasks", quality: "authored", label: "观察任务", blocks: ["task", "task", "task", "task"] },
    { id: "next", quality: "authored", label: "复述延伸", blocks: ["speak", "parent", "related"] },
  ],
);

const allBlocks = viewModel.stages.flatMap((stage) => stage.blocks);
assert.ok(allBlocks.length >= viewModel.stages.length, "each stage should expose at least one renderable block");

const taskBlock = allBlocks.find((block) => block.kind === "task");
assert.ok(taskBlock, "cicada-life should expose a normalized task block");
assert.equal(taskBlock.visual.imageVisibility, "always");
assert.ok(taskBlock.nodes.length > 0, "task block should expose normalized task option nodes");
assert.ok(
  taskBlock.nodes.some((node) => node.evidence.resolution === "explicit"),
  "task nodes should preserve explicit visual evidence bindings",
);
assert.ok(
  taskBlock.nodes.every((node) => node.evidence.visualSlotId && node.evidence.focusRegionId),
  "task nodes should expose resolved visual slot and focus region ids",
);

const strictViewModel = normalizeTopicInteraction(topic, {
  locale: "zh-CN",
  mode: "production",
  platform: "web",
  strictEvidence: true,
});

assert.ok(
  strictViewModel.diagnostics.errors.length === 0,
  `cicada-life strict diagnostics should pass after focus migration: ${strictViewModel.diagnostics.errors.join("; ")}`,
);
assert.ok(Array.isArray(strictViewModel.diagnostics.warnings));

const missingFocusTopic = structuredClone(topic);
const sequenceBinding = missingFocusTopic.visualEvidenceBindings?.find(
  (binding) => binding.source === "clickTasks.cicada-sequence-01.options.egg",
);
assert.ok(sequenceBinding, "sequence option binding should exist before mutation");
delete sequenceBinding.focus;

const missingFocusViewModel = normalizeTopicInteraction(missingFocusTopic, {
  locale: "zh-CN",
  mode: "production",
  platform: "web",
  strictEvidence: true,
});

assert.ok(
  missingFocusViewModel.diagnostics.errors.some((error) => error === "tasks/cicada-sequence-01/egg missing focus region (derived)"),
  "strict diagnostics should report explicit bindings that lack focus regions",
);

const materializedTopic = structuredClone(topic);
for (const binding of materializedTopic.visualEvidenceBindings ?? []) {
  delete binding.focus;
}
const materialized = materializeVisualEvidenceFocus(materializedTopic, { locale: "zh-CN" });
assert.ok(materialized.changed > 0, "focus materialization should fill bindings that lack focus");
assert.deepEqual(materialized.missingSources, []);
const materializedViewModel = normalizeTopicInteraction(materialized.topic, {
  locale: "zh-CN",
  mode: "production",
  platform: "web",
  strictEvidence: true,
});
assert.deepEqual(materializedViewModel.diagnostics.errors, []);

const enTopic = getTopic("cicada-life", "en-US");
assert.ok(enTopic, "cicada-life English topic should exist");
const enViewModel = normalizeTopicInteraction(enTopic, {
  locale: "en-US",
  mode: "dev",
  platform: "web",
});
assert.deepEqual(
  enViewModel.stages.map((stage) => stage.label),
  [
    "Real Discovery",
    "Recognize the Nymph",
    "Life Cycle",
    "Molting Process",
    "Common Mix-ups",
    "Observation Tasks",
    "Retell and Extend",
  ],
);

console.log("normalize topic interaction view model checks passed");
