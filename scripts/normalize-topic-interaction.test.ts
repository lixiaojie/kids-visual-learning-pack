import assert from "node:assert/strict";
import { getTopic, normalizeTopicInteraction } from "../packages/kids-content/src/index";

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
    blocks: stage.blocks.map((block) => block.kind),
  })),
  [
    { id: "observe", quality: "fallback", blocks: ["hero"] },
    { id: "classify", quality: "fallback", blocks: ["classification", "classification", "classification"] },
    { id: "inspect", quality: "fallback", blocks: ["objects", "objects", "objects"] },
    { id: "trace", quality: "fallback", blocks: ["mechanism", "mechanism"] },
    { id: "compare", quality: "fallback", blocks: ["compare", "compare", "compare"] },
    { id: "tasks", quality: "fallback", blocks: ["task", "task", "task", "task"] },
    { id: "next", quality: "fallback", blocks: ["speak", "parent", "related"] },
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
  strictViewModel.diagnostics.errors.some((error) => error.includes("missing focus region (derived)")),
  "strict diagnostics should expose current derived focus-region gaps before cicada-life migration",
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

console.log("normalize topic interaction view model checks passed");
