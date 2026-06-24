import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const errors = [];

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), "utf8");
}

const webTopicPage = read("boards/kids-world/src/pages/TopicPage.tsx");
const webSceneDeckPath = "boards/kids-world/src/components/topic/SceneDeckTopicPage.tsx";
const miniRuntimePage = read("apps/miniprogram/src/components/topic/TopicRuntimePage.tsx");
const miniSceneDeckPath = "apps/miniprogram/src/components/topic/SceneDeckTopicPage.tsx";
const packageJson = read("package.json");

for (const [label, source, componentPath] of [
  ["Web", webTopicPage, webSceneDeckPath],
  ["Mini Program", miniRuntimePage, miniSceneDeckPath],
]) {
  if (source.includes("learningScenes?.length")) {
    errors.push(`${label} topic runtime must not gate scene deck rendering on authored learningScenes; scene-deck fallback should cover all topics`);
  }
  if (!source.includes("SceneDeckTopicPage")) {
    errors.push(`${label} topic runtime must render SceneDeckTopicPage`);
  }
  if (!fs.existsSync(path.join(root, componentPath))) {
    errors.push(`${label} scene deck component is missing: ${componentPath}`);
  }
  for (const legacyRuntimeToken of [
    "createInitialTopicInteractionState",
    "reduceTopicInteractionState",
    "resolveTopicPresentation",
    "LearningFlowRail",
    "ClickTaskDeck",
    "getTopicLearningFlow",
  ]) {
    if (source.includes(legacyRuntimeToken)) {
      errors.push(`${label} topic runtime must not import legacy detail runtime token: ${legacyRuntimeToken}`);
    }
  }
}

for (const componentPath of [webSceneDeckPath, miniSceneDeckPath]) {
  if (!fs.existsSync(path.join(root, componentPath))) continue;
  const source = read(componentPath);
  for (const required of [
    "normalizeTopicToSceneDeck",
    "createInitialSceneInteractionState",
    "reduceSceneInteractionState",
    "resolveScenePresentation",
    "SELECT_SCENE",
    "SELECT_FOCUS",
    "CLICK_TASK_OPTION",
    "scene-deck",
  ]) {
    if (!source.includes(required)) {
      errors.push(`${componentPath} must wire ${required}`);
    }
  }
}

if (!packageJson.includes("validate:scene-ui")) {
  errors.push("package.json must expose validate:scene-ui");
}
if (!packageJson.includes("npm run validate:scene-ui")) {
  errors.push("package.json validate must include validate:scene-ui");
}

if (errors.length > 0) {
  console.error("scene UI validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log("scene UI checked");
