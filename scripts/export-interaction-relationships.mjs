import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const outDir = path.join(root, "tmp", "interaction-relationships");

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(root, relativePath), "utf8"));
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function optionNodes(task) {
  const options =
    task.options ??
    [...(task.targetIds ?? []), ...(task.decoyIds ?? [])].map((id) => ({
      id,
      label: id.replace(/-/g, " "),
    }));
  return options.map((option) => ({
    id: option.id,
    label: option.label,
    source: `clickTasks.${task.id}.options.${option.id}`,
  }));
}

function bindingMap(topic) {
  return new Map((topic.visualEvidenceBindings ?? []).map((binding) => [binding.source, binding]));
}

function slotMap(topic) {
  return new Map((topic.visualSlots ?? []).map((slot) => [slot.id, slot]));
}

function visualFor(topic, source) {
  const bindings = bindingMap(topic);
  const slots = slotMap(topic);
  const binding = bindings.get(source);
  const slot = binding ? slots.get(binding.visualSlotId) : null;
  return {
    source,
    evidenceTitle: binding?.evidenceTitle ?? null,
    visualSlotId: binding?.visualSlotId ?? null,
    assetId: slot?.assetId ?? null,
    focusMode: binding?.focus?.mode ?? null,
    activeRegionIds: binding?.focus?.activeRegionIds ?? [],
  };
}

function subflow(id, label, source, secondaryNodes = [], extra = {}) {
  return {
    id,
    label,
    source,
    ...extra,
    secondaryNodes,
  };
}

function buildRelationship(topic) {
  const objectByGroup = new Map();
  for (const object of topic.representativeObjects ?? []) {
    const list = objectByGroup.get(object.groupId) ?? [];
    list.push(object);
    objectByGroup.set(object.groupId, list);
  }

  const stages = [];

  stages.push({
    id: "observe",
    label: "发现它",
    defaultSource: "hero",
    relationshipShape: "main-only",
    subflows: [
      subflow("hero", topic.hero?.title ?? topic.title, "hero", [], {
        visual: topic.visualSlots?.find((slot) => slot.target === "hero") ?? null,
      }),
    ],
  });

  stages.push({
    id: "classify",
    label: "认出它",
    defaultSource: topic.classificationGroups?.[0] ? `classificationGroups.${topic.classificationGroups[0].id}` : null,
    relationshipShape: "main -> classification group -> representative objects",
    subflows: (topic.classificationGroups ?? []).map((group) =>
      subflow(
        group.id,
        group.name,
        `classificationGroups.${group.id}`,
        (objectByGroup.get(group.id) ?? []).map((object) => ({
          id: object.id,
          label: object.name,
          source: `representativeObjects.${object.id}`,
          visual: visualFor(topic, `representativeObjects.${object.id}`),
        })),
        { visual: visualFor(topic, `classificationGroups.${group.id}`) },
      ),
    ),
  });

  stages.push({
    id: "inspect",
    label: "看懂它",
    defaultSource: topic.representativeObjects?.[0] ? `representativeObjects.${topic.representativeObjects[0].id}` : null,
    relationshipShape: "main -> object group -> representative objects",
    note: "This currently duplicates the classify container structure because object detail nodes are grouped by classificationGroup.",
    subflows: (topic.classificationGroups ?? []).map((group) =>
      subflow(
        group.id,
        group.name,
        `classificationGroups.${group.id}`,
        (objectByGroup.get(group.id) ?? []).map((object) => ({
          id: object.id,
          label: object.name,
          source: `representativeObjects.${object.id}`,
          visual: visualFor(topic, `representativeObjects.${object.id}`),
        })),
        { visual: visualFor(topic, `classificationGroups.${group.id}`) },
      ),
    ),
  });

  stages.push({
    id: "trace",
    label: "追踪它",
    defaultSource: topic.mechanism?.steps?.[0] ? `mechanism.steps.${topic.mechanism.steps[0].id}` : null,
    relationshipShape: "main -> mechanism container -> mechanism steps",
    subflows: [
      subflow(
        "mechanism",
        topic.mechanism?.title ?? "机制步骤",
        "mechanism",
        (topic.mechanism?.steps ?? []).map((step) => ({
          id: step.id,
          label: step.shortTitle,
          source: `mechanism.steps.${step.id}`,
          visual: visualFor(topic, `mechanism.steps.${step.id}`),
        })),
        { visualSlotId: topic.visualSlots?.find((slot) => slot.target === "mechanism")?.id ?? null },
      ),
      ...(topic.secondaryMechanism
        ? [
            subflow(
              "secondaryMechanism",
              topic.secondaryMechanism.title,
              "secondaryMechanism",
              topic.secondaryMechanism.steps.map((step) => ({
                id: step.id,
                label: step.shortTitle,
                source: `secondaryMechanism.steps.${step.id}`,
                visual: visualFor(topic, `secondaryMechanism.steps.${step.id}`),
              })),
              { visualSlotId: topic.visualSlots?.find((slot) => slot.target === "secondaryMechanism")?.id ?? null },
            ),
          ]
        : []),
    ],
  });

  stages.push({
    id: "compare",
    label: "比一比",
    defaultSource: topic.comparePairs?.[0] ? `comparePairs.${topic.comparePairs[0].id}` : null,
    relationshipShape: "main -> compare pair -> compared sides",
    subflows: (topic.comparePairs ?? []).map((pair) =>
      subflow(
        pair.id,
        pair.title,
        `comparePairs.${pair.id}`,
        [
          { id: "a", label: pair.a.name, source: `comparePairs.${pair.id}#a`, visual: visualFor(topic, `comparePairs.${pair.id}`) },
          { id: "b", label: pair.b.name, source: `comparePairs.${pair.id}#b`, visual: visualFor(topic, `comparePairs.${pair.id}`) },
        ],
        { visual: visualFor(topic, `comparePairs.${pair.id}`) },
      ),
    ),
  });

  stages.push({
    id: "tasks",
    label: "做任务",
    defaultSource: topic.clickTasks?.[0] ? `clickTasks.${topic.clickTasks[0].id}` : null,
    relationshipShape: "main -> click task -> answer options",
    subflows: (topic.clickTasks ?? []).map((task) =>
      subflow(
        task.id,
        task.title,
        `clickTasks.${task.id}`,
        optionNodes(task).map((option) => ({
          ...option,
          visual: visualFor(topic, option.source),
        })),
        {
          type: task.type,
          visual: topic.visualSlots?.find((slot) => slot.target === `clickTasks.${task.id}`) ??
            topic.visualSlots?.find((slot) => slot.target === "clickTasks") ??
            null,
        },
      ),
    ),
  });

  stages.push({
    id: "next",
    label: "继续看",
    defaultSource: null,
    relationshipShape: "main -> summary/parent/related containers",
    subflows: [
      subflow("speak", "表达模板", "speakTemplates"),
      subflow("parent", "家长提示", "parentTips", [], {
        visual: topic.visualSlots?.find((slot) => slot.target === "parentTips") ?? null,
      }),
      subflow("related", "相关主题", "relatedTopics"),
    ],
  });

  return {
    slug: topic.slug,
    title: topic.title,
    expectedHierarchy: "mainFlowStage -> subflowContainer -> secondaryNode -> visual/evidence",
    stages,
  };
}

function markdownForTopic(relationship) {
  const lines = [
    `# ${relationship.title} (${relationship.slug}) Interaction Relationships`,
    "",
    `Expected hierarchy: \`${relationship.expectedHierarchy}\``,
    "",
  ];

  for (const stage of relationship.stages) {
    lines.push(`## ${stage.label} / ${stage.id}`);
    lines.push(`- defaultSource: \`${stage.defaultSource ?? "none"}\``);
    lines.push(`- shape: ${stage.relationshipShape}`);
    if (stage.note) lines.push(`- note: ${stage.note}`);
    lines.push("");

    for (const flow of stage.subflows) {
      lines.push(`### ${flow.label} / ${flow.id}`);
      lines.push(`- source: \`${flow.source ?? "none"}\``);
      if (flow.type) lines.push(`- type: \`${flow.type}\``);
      if (flow.visual?.assetId || flow.visual?.visualSlotId) {
        lines.push(`- visual: slot=\`${flow.visual.visualSlotId ?? flow.visual.id ?? "none"}\`, asset=\`${flow.visual.assetId ?? "none"}\``);
      }
      if (!flow.secondaryNodes?.length) {
        lines.push("- secondaryNodes: none");
      } else {
        lines.push("- secondaryNodes:");
        for (const node of flow.secondaryNodes) {
          lines.push(
            `  - \`${node.id}\` ${node.label}: source=\`${node.source}\`, slot=\`${node.visual?.visualSlotId ?? "none"}\`, asset=\`${node.visual?.assetId ?? "none"}\`, focus=\`${node.visual?.focusMode ?? "none"}:${(node.visual?.activeRegionIds ?? []).join("|")}\``,
          );
        }
      }
      lines.push("");
    }
  }

  return `${lines.join("\n")}\n`;
}

ensureDir(outDir);

const registry = readJson("boards/kids-world/src/data/topic-registry.json");
const slugs = registry.topics
  .filter((topic) => topic.status === "render-ready" || topic.contentStatus === "render-ready")
  .map((topic) => topic.slug);
const relationships = slugs.map((slug) => buildRelationship(readJson(`boards/kids-world/src/data/topics/${slug}.json`)));

fs.writeFileSync(path.join(outDir, "all-topics.interaction-relationships.json"), `${JSON.stringify(relationships, null, 2)}\n`);
for (const relationship of relationships) {
  fs.writeFileSync(path.join(outDir, `${relationship.slug}.interaction-relationships.md`), markdownForTopic(relationship));
}

console.log(`Exported ${relationships.length} topic interaction relationship reports to ${path.relative(root, outDir)}`);
