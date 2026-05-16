import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const errors = [];
const warnings = [];

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(root, relativePath), "utf8"));
}

function requireFile(relativePath) {
  if (!fs.existsSync(path.join(root, relativePath))) {
    errors.push(`missing shared interaction graph module: ${relativePath}`);
  }
}

for (const file of [
  "packages/kids-content/src/focus.ts",
  "packages/kids-content/src/interaction-graph.ts",
  "packages/kids-content/src/interaction-state.ts",
  "packages/kids-content/src/interaction-validation.ts",
]) {
  requireFile(file);
}

const robots = readJson("boards/kids-world/src/data/topics/robots.json");
const bindings = new Map((robots.visualEvidenceBindings ?? []).map((binding) => [binding.source, binding]));
const robotObjectIds = robots.representativeObjects.map((object) => object.id);
const expectedRobotObjectIds = ["camera", "microphone", "distance-sensor", "button", "program", "wheel-arm"];
if (robotObjectIds.join("|") !== expectedRobotObjectIds.join("|")) {
  errors.push(`robots object cards must match the 6-card visual: expected ${expectedRobotObjectIds.join(", ")}, got ${robotObjectIds.join(", ")}`);
}
const robotFindTask = robots.clickTasks.find((task) => task.id === "robot-find-01");
const robotFindOptions = [...(robotFindTask?.targetIds ?? []), ...(robotFindTask?.decoyIds ?? [])];
if (robotFindOptions.join("|") !== expectedRobotObjectIds.join("|")) {
  errors.push(`robots robot-find-01 options must match object cards: expected ${expectedRobotObjectIds.join(", ")}, got ${robotFindOptions.join(", ")}`);
}
if (!robots.visualSlots?.some((slot) => slot.id === "robot-find-object-cards" && slot.assetId === "human-system-robots-object-icons")) {
  errors.push("robots robot-find-01 must use the 6-card object visual slot");
}

function checkRobotsSource(source, expectedSlot, expectedMode, expectedRegions) {
  const binding = bindings.get(source);
  if (!binding) {
    errors.push(`robots missing binding for ${source}`);
    return;
  }
  const actualRegions = binding.focus?.activeRegionIds ?? [];
  if (binding.visualSlotId !== expectedSlot) {
    errors.push(`robots ${source} expected slot ${expectedSlot}, got ${binding.visualSlotId}`);
  }
  if (binding.focus?.mode !== expectedMode) {
    errors.push(`robots ${source} expected focus ${expectedMode}, got ${binding.focus?.mode ?? "none"}`);
  }
  if (expectedRegions.join("|") !== actualRegions.join("|")) {
    errors.push(`robots ${source} expected regions ${expectedRegions.join("|")}, got ${actualRegions.join("|")}`);
  }
}

checkRobotsSource("mechanism.steps.input", "mechanism", "path-step", ["input"]);
checkRobotsSource("mechanism.steps.decide", "mechanism", "path-step", ["decide"]);
checkRobotsSource("secondaryMechanism.steps.sense-wall", "mechanism", "path-step", ["input"]);
checkRobotsSource("clickTasks.robot-sequence-01.options.act", "click-task", "sequence-progress", ["act"]);
checkRobotsSource("representativeObjects.wheel-arm", "object-icons", "hotspot", ["wheel-arm"]);
checkRobotsSource("clickTasks.robot-find-01.options.wheel-arm", "robot-find-object-cards", "hotspot", ["wheel-arm"]);

for (const source of ["comparePairs.robot-vs-remote-toy", "comparePairs.sensor-vs-actuator"]) {
  const binding = bindings.get(source);
  if (!binding?.focus?.activeRegionIds?.includes("left") || !binding.focus.activeRegionIds.includes("right")) {
    errors.push(`robots ${source} pair focus must include left and right`);
  }
}

const registry = readJson("boards/kids-world/src/data/topic-registry.json");
const slugs = registry.topics
  .filter((topic) => topic.status === "render-ready" || topic.contentStatus === "render-ready")
  .map((topic) => topic.slug);

for (const slug of slugs) {
  const topic = readJson(`boards/kids-world/src/data/topics/${slug}.json`);
  if (!topic.visualSlots?.some((slot) => slot.target === "hero")) warnings.push(`${slug} has no hero visual slot`);
  if (!topic.clickTasks?.length) warnings.push(`${slug} has no clickTasks for tasks stage`);
}

if (errors.length > 0) {
  console.error("interaction graph validation failed:");
  for (const error of errors) console.error(`[ERROR] ${error}`);
  for (const warning of warnings) console.warn(`[WARN] ${warning}`);
  process.exit(1);
}

for (const warning of warnings) console.warn(`[WARN] ${warning}`);
console.log(`interaction graph seed validation checked ${slugs.length} topics`);
