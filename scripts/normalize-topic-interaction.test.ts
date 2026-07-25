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
assert.equal(viewModel.stages.length, 5, "view model should expose the authored five-stage scene flow");
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
    {
      id: "classify",
      quality: "authored",
      label: "认出它",
      blocks: ["classification", "classification", "classification", "objects", "objects", "objects"],
    },
    { id: "trace", quality: "authored", label: "看变化", blocks: ["mechanism", "mechanism"] },
    {
      id: "compare",
      quality: "authored",
      label: "比一比",
      blocks: ["compare", "compare", "compare", "task", "task", "task", "task"],
    },
    { id: "next", quality: "authored", label: "复述延伸", blocks: ["speak", "parent", "related"] },
  ],
);

const reorderedFlowTopic = structuredClone(topic);
reorderedFlowTopic.learningFlow = [
  reorderedFlowTopic.learningFlow?.find((stage) => stage.id === "observe"),
  reorderedFlowTopic.learningFlow?.find((stage) => stage.id === "trace"),
  reorderedFlowTopic.learningFlow?.find((stage) => stage.id === "classify"),
  reorderedFlowTopic.learningFlow?.find((stage) => stage.id === "compare"),
  reorderedFlowTopic.learningFlow?.find((stage) => stage.id === "next"),
].filter((stage): stage is NonNullable<typeof stage> => Boolean(stage));
const reorderedViewModel = normalizeTopicInteraction(reorderedFlowTopic, {
  locale: "zh-CN",
  mode: "dev",
  platform: "web",
});
assert.deepEqual(
  Object.fromEntries(
    reorderedViewModel.stages.map((stage) => [stage.id, stage.blocks.map((block) => block.kind)]),
  ),
  {
    observe: ["hero"],
    trace: ["mechanism", "mechanism"],
    classify: ["classification", "classification", "classification", "objects", "objects", "objects"],
    compare: ["compare", "compare", "compare", "task", "task", "task", "task"],
    next: ["speak", "parent", "related"],
  },
  "collapsed graph stages should follow canonical graph ownership without duplicating blocks when authored navigation is reordered",
);

const allBlocks = viewModel.stages.flatMap((stage) => stage.blocks);
assert.ok(allBlocks.length >= viewModel.stages.length, "each stage should expose at least one renderable block");
assert.equal(
  new Set(allBlocks.map((block) => block.id)).size,
  allBlocks.length,
  "collapsed graph stages must keep block ids unique",
);

const duplicateFlowTopic = structuredClone(topic);
const duplicateStage = duplicateFlowTopic.learningFlow?.[0];
assert.ok(duplicateStage, "authored learning flow should expose a stage to duplicate");
duplicateFlowTopic.learningFlow = [...(duplicateFlowTopic.learningFlow ?? []), structuredClone(duplicateStage)];
assert.throws(
  () => normalizeTopicInteraction(duplicateFlowTopic, { locale: "zh-CN", mode: "production" }),
  /duplicate authored learning flow stage: observe/,
);

const unknownFlowTopic = structuredClone(topic);
assert.ok(unknownFlowTopic.learningFlow?.[0], "authored learning flow should expose a stage to mutate");
unknownFlowTopic.learningFlow[0].id = "unknown-stage";
assert.throws(
  () => normalizeTopicInteraction(unknownFlowTopic, { locale: "zh-CN", mode: "production" }),
  /unknown authored learning flow stage: unknown-stage/,
);

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
  missingFocusViewModel.diagnostics.errors.some((error) => error === "compare/cicada-sequence-01/egg missing focus region (derived)"),
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
    "Recognize It",
    "Watch Change",
    "Compare",
    "Retell and Extend",
  ],
);

console.log("normalize topic interaction view model checks passed");
