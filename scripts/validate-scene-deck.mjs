import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { spawnSync } from "node:child_process";

const root = process.cwd();
const errors = [];

const requiredExports = [
  "normalizeTopicToSceneDeck",
  "createInitialSceneInteractionState",
  "reduceSceneInteractionState",
  "resolveScenePresentation",
  "resolveSceneEvidence",
  "SceneDeckViewModel",
  "SceneInteractionState",
  "ScenePresentation",
];

const sceneDeckPath = path.join(root, "packages/kids-content/src/scene-deck.ts");
const topicTypesPath = path.join(root, "boards/kids-world/src/types/topic.ts");
const sceneTestPath = path.join(root, "scripts/scene-deck.test.ts");

for (const filePath of [sceneDeckPath, topicTypesPath, sceneTestPath]) {
  if (!fs.existsSync(filePath)) {
    errors.push(`Missing scene deck file: ${path.relative(root, filePath)}`);
  }
}

const sceneDeckSource = fs.existsSync(sceneDeckPath) ? fs.readFileSync(sceneDeckPath, "utf8") : "";
for (const exportedName of requiredExports) {
  if (!sceneDeckSource.includes(exportedName)) {
    errors.push(`packages/kids-content/src/scene-deck.ts does not export ${exportedName}`);
  }
}

const topicTypesSource = fs.existsSync(topicTypesPath) ? fs.readFileSync(topicTypesPath, "utf8") : "";
for (const requiredType of ["LearningScene", "SceneVisualPlan", "FocusItem", "SceneTask", "SceneTaskOption"]) {
  if (!topicTypesSource.includes(requiredType)) {
    errors.push(`boards/kids-world/src/types/topic.ts does not define ${requiredType}`);
  }
}

if (errors.length === 0) {
  const result = spawnSync(path.join(root, "node_modules/.bin/sucrase-node"), [sceneTestPath], {
    cwd: root,
    encoding: "utf8",
  });
  if (result.status !== 0) {
    errors.push(`scene deck behavior test failed:\n${result.stdout}${result.stderr}`);
  }
}

if (errors.length > 0) {
  console.error("scene deck validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log("scene deck validation passed");
