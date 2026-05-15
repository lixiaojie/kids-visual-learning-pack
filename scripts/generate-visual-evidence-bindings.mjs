import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const topicsDir = path.join(root, "boards/kids-world/src/data/topics");
const registryPath = path.join(root, "boards/kids-world/src/data/topic-registry.json");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

function deepMerge(base, overlay) {
  if (!overlay) return base;
  if (Array.isArray(base) || Array.isArray(overlay)) {
    if (
      Array.isArray(base) &&
      Array.isArray(overlay) &&
      base.every((item) => item && typeof item === "object" && "id" in item) &&
      overlay.every((item) => item && typeof item === "object" && "id" in item)
    ) {
      const baseById = new Map(base.map((item) => [item.id, item]));
      return overlay.map((item) => (baseById.has(item.id) ? deepMerge(baseById.get(item.id), item) : item));
    }
    return overlay;
  }
  if (typeof base !== "object" || typeof overlay !== "object" || base === null || overlay === null) return overlay;

  const result = { ...base };
  for (const [key, value] of Object.entries(overlay)) {
    result[key] = key in result ? deepMerge(result[key], value) : value;
  }
  return result;
}

function renderReadySlugs() {
  const registry = readJson(registryPath);
  return registry.topics
    .filter((topic) => topic.status === "render-ready" || topic.contentStatus === "render-ready")
    .map((topic) => topic.slug);
}

function firstSlot(topic, predicates) {
  const slots = topic.visualSlots ?? [];
  for (const predicate of predicates) {
    const slot = slots.find(predicate);
    if (slot) return slot;
  }
  throw new Error(`${topic.slug}: no visualSlot available for evidence binding`);
}

function slotForSource(topic, source) {
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

function optionList(task) {
  return (
    task.options ??
    [...(task.targetIds ?? []), ...(task.decoyIds ?? [])].map((id) => ({
      id,
      label: id.replace(/-/g, " "),
    }))
  );
}

function optionStatus(task, optionId) {
  if (task.type === "singleChoice") return optionId === task.correctOptionId ? "correct" : "wrong";
  if (task.type === "findTarget") return task.targetIds?.includes(optionId) ? "partial" : "wrong";
  if (task.type === "sequenceClick") return task.correctSequence?.includes(optionId) ? "partial" : "wrong";
  return "selected";
}

function copy(locale) {
  return locale === "en-US"
    ? {
        groupPrompt: "Look for objects that belong to this group.",
        groupCopy: (explanation, names) => (names.length ? `${explanation} You can spot: ${names.join(", ")}.` : explanation),
        groupChip: "Belongs to this group",
        objectPrompt: "Look for visual clues for this object.",
        objectChip: "Current object",
        mainStepPrompt: (index) => `Current step ${index + 1}. Look at what happens here.`,
        secondaryStepPrompt: (index) => `Current step ${index + 1}. Observe this supporting mechanism.`,
        stepChip: (index) => `Step ${index + 1}`,
        comparePrompt: (a, b) => `Compare visual clues for ${a} and ${b}.`,
        compareCopy: (pair) => `${pair.a.name}: ${pair.a.points.join("; ")}. ${pair.b.name}: ${pair.b.points.join("; ")}. ${pair.childConclusion}`,
        compareA: "Compare object A",
        compareB: "Compare object B",
        taskFallback: "Go back to the picture and find one more clue.",
        currentChoice: "Current choice",
        needsObserve: "Look again",
        sequenceCopy: (label, task) => `Current step: ${label}. ${task.prompt ?? task.title}`,
      }
    : {
        groupPrompt: "看一看哪些对象被归到这一类。",
        groupCopy: (explanation, names) => (names.length ? `${explanation} 这类里可以看到：${names.join("、")}。` : explanation),
        groupChip: "属于当前分类",
        objectPrompt: "看图找这个对象的线索。",
        objectChip: "当前观察对象",
        mainStepPrompt: (index) => `当前第 ${index + 1} 步，先看这一步发生了什么。`,
        secondaryStepPrompt: (index) => `当前第 ${index + 1} 步，观察这个补充机制。`,
        stepChip: (index) => `第 ${index + 1} 步`,
        comparePrompt: (a, b) => `对比 ${a} 和 ${b} 的图片线索。`,
        compareCopy: (pair) => `${pair.a.name}: ${pair.a.points.join("；")}。${pair.b.name}: ${pair.b.points.join("；")}。${pair.childConclusion}`,
        compareA: "对比对象 A",
        compareB: "对比对象 B",
        taskFallback: "再回到图片里找一个线索。",
        currentChoice: "当前选择",
        needsObserve: "需要再观察",
        sequenceCopy: (label, task) => `当前步骤：${label}。${task.prompt ?? task.title}`,
      };
}

function binding(topic, source, data) {
  const slot = slotForSource(topic, source);
  return {
    id: `evidence-${source.replaceAll(".", "-")}`,
    source,
    visualSlotId: slot.id,
    interactionScope: "local",
    evidenceTitle: data.title,
    observePrompt: data.prompt,
    evidenceCopy: data.copy,
    markerChips: data.chips,
    expectedStatus: data.status ?? "selected",
    quality: "generated",
  };
}

function bindingsForTopic(topic, locale = "zh-CN") {
  const bindings = [];
  const text = copy(locale);

  for (const group of topic.classificationGroups ?? []) {
    const objectNames = (topic.representativeObjects ?? [])
      .filter((object) => object.groupId === group.id)
      .map((object) => object.name);
    bindings.push(
      binding(topic, `classificationGroups.${group.id}`, {
        title: group.name,
        prompt: text.groupPrompt,
        copy: text.groupCopy(group.childExplanation, objectNames),
        chips: objectNames.slice(0, 4).map((name) => ({ label: name, meaning: text.groupChip, emphasis: "supporting" })),
      }),
    );
  }

  for (const object of topic.representativeObjects ?? []) {
    bindings.push(
      binding(topic, `representativeObjects.${object.id}`, {
        title: object.name,
        prompt: object.visualHint || text.objectPrompt,
        copy: object.childExplanation,
        chips: [{ label: object.name, meaning: object.commonMisread || text.objectChip, emphasis: "primary" }],
      }),
    );
  }

  for (const [index, step] of (topic.mechanism?.steps ?? []).entries()) {
    bindings.push(
      binding(topic, `mechanism.steps.${step.id}`, {
        title: step.shortTitle,
        prompt: text.mainStepPrompt(index),
        copy: step.childExplanation,
        chips: [{ label: text.stepChip(index), meaning: step.shortTitle, emphasis: "primary" }],
      }),
    );
  }

  for (const [index, step] of (topic.secondaryMechanism?.steps ?? []).entries()) {
    bindings.push(
      binding(topic, `secondaryMechanism.steps.${step.id}`, {
        title: step.shortTitle,
        prompt: text.secondaryStepPrompt(index),
        copy: step.childExplanation,
        chips: [{ label: text.stepChip(index), meaning: step.shortTitle, emphasis: "primary" }],
      }),
    );
  }

  for (const pair of topic.comparePairs ?? []) {
    bindings.push(
      binding(topic, `comparePairs.${pair.id}`, {
        title: pair.title,
        prompt: text.comparePrompt(pair.a.name, pair.b.name),
        copy: text.compareCopy(pair),
        chips: [
          { label: pair.a.name, meaning: pair.a.points[0] ?? text.compareA, emphasis: "primary" },
          { label: pair.b.name, meaning: pair.b.points[0] ?? text.compareB, emphasis: "supporting" },
        ],
      }),
    );
  }

  for (const task of topic.clickTasks ?? []) {
    for (const option of optionList(task)) {
      const status = optionStatus(task, option.id);
      const wrongHint = task.wrongHints?.[option.id] ?? task.wrongHint;
      const sequenceCopy = task.type === "sequenceClick" && status !== "wrong" ? text.sequenceCopy(option.label, task) : null;
      bindings.push(
        binding(topic, `clickTasks.${task.id}.options.${option.id}`, {
          title: option.label,
          prompt: task.prompt ?? task.title,
          copy: status === "wrong" ? wrongHint ?? text.taskFallback : sequenceCopy ?? task.successCopy ?? task.prompt ?? task.title,
          status,
          chips: [{ label: option.label, meaning: status === "wrong" ? text.needsObserve : text.currentChoice, emphasis: status === "wrong" ? "warning" : "primary" }],
        }),
      );
    }
  }

  return bindings;
}

for (const slug of renderReadySlugs()) {
  const filePath = path.join(topicsDir, `${slug}.json`);
  const topic = readJson(filePath);
  topic.visualEvidenceBindings = bindingsForTopic(topic, "zh-CN");
  writeJson(filePath, topic);
  console.log(`${slug}: ${topic.visualEvidenceBindings.length} visualEvidenceBindings`);

  const overlayPath = path.join(root, "boards/kids-world/src/data/locales/en-US/topics", `${slug}.json`);
  const overlay = readJson(overlayPath);
  const mergedTopic = deepMerge(topic, overlay);
  overlay.visualEvidenceBindings = bindingsForTopic(mergedTopic, "en-US");
  writeJson(overlayPath, overlay);
  console.log(`${slug}: ${overlay.visualEvidenceBindings.length} en-US visualEvidenceBindings`);
}
