import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const root = process.cwd();
const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "content-alignment-validation-"));

function copyFixturePath(relativePath) {
  const source = path.join(root, relativePath);
  const destination = path.join(fixtureRoot, relativePath);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.cpSync(source, destination, { recursive: true });
}

function runValidator() {
  return spawnSync(process.execPath, ["scripts/validate-content-alignment.mjs"], {
    cwd: fixtureRoot,
    encoding: "utf8",
  });
}

try {
  for (const relativePath of [
    "scripts/validate-content-alignment.mjs",
    "channel-policy.json",
    "boards/kids-world/src",
    "packages/kids-content/src",
    "apps/miniprogram/src",
    "apps/miniprogram/config",
  ]) {
    copyFixturePath(relativePath);
  }

  const validResult = runValidator();
  assert.equal(
    validResult.status,
    0,
    `current Scene Deck alignment should pass:\n${validResult.stderr}${validResult.stdout}`,
  );
  if (validResult.stdout) process.stdout.write(validResult.stdout);
  if (validResult.stderr) process.stderr.write(validResult.stderr);

  const webEntryPath = path.join(fixtureRoot, "boards/kids-world/src/pages/TopicPage.tsx");
  const originalWebEntry = fs.readFileSync(webEntryPath, "utf8");
  const commentOnlyWebEntry = originalWebEntry.replace(
    "return <SceneDeckTopicPage topic={topic} locale={locale} />;",
    "return <main />; // SceneDeckTopicPage",
  );
  assert.notEqual(commentOnlyWebEntry, originalWebEntry, "controlled fixture should remove the Scene Deck JSX render");
  fs.writeFileSync(webEntryPath, commentOnlyWebEntry);

  const commentOnlyResult = runValidator();
  assert.equal(commentOnlyResult.status, 1, "an import or comment without SceneDeckTopicPage JSX must fail");
  assert.match(commentOnlyResult.stderr, /Web topic runtime must render SceneDeckTopicPage/);

  const stringOnlyWebEntry = originalWebEntry.replace(
    "return <SceneDeckTopicPage topic={topic} locale={locale} />;",
    'return <main data-probe={"<SceneDeckTopicPage />"} />;',
  );
  assert.notEqual(stringOnlyWebEntry, originalWebEntry, "controlled fixture should replace JSX with a string literal");
  fs.writeFileSync(webEntryPath, stringOnlyWebEntry);

  const stringOnlyResult = runValidator();
  assert.equal(stringOnlyResult.status, 1, "a string literal that looks like SceneDeckTopicPage JSX must fail");
  assert.match(stringOnlyResult.stderr, /Web topic runtime must render SceneDeckTopicPage/);

  fs.writeFileSync(webEntryPath, originalWebEntry);
  const topicPath = path.join(
    fixtureRoot,
    "boards/kids-world/src/data/topics/animal-classification-tree.json",
  );
  const originalTopicSource = fs.readFileSync(topicPath, "utf8");
  const topic = JSON.parse(originalTopicSource);
  const compareScene = topic.learningScenes.find((scene) => scene.sceneType === "compare-split");
  assert.ok(compareScene, "controlled fixture should expose a compare-split scene");
  const unrelatedObjectSource = `representativeObjects.${topic.representativeObjects[0].id}`;
  for (const focus of compareScene.focusItems) {
    focus.source = unrelatedObjectSource;
  }
  fs.writeFileSync(topicPath, `${JSON.stringify(topic, null, 2)}\n`);

  const unrelatedCompareResult = runValidator();
  assert.equal(unrelatedCompareResult.status, 1, "compare scenes without comparePairs focus evidence must fail");
  assert.match(
    unrelatedCompareResult.stderr,
    /animal-classification-tree compare-split scene must focus comparePairs evidence/,
  );

  const emptyExplanationTopic = JSON.parse(originalTopicSource);
  const emptyExplanationScene = emptyExplanationTopic.learningScenes.find(
    (scene) => scene.sceneType === "compare-split",
  );
  assert.ok(emptyExplanationScene, "controlled fixture should expose compare content to empty");
  emptyExplanationScene.contentBlocks = [
    { id: "empty-compare-copy", type: "short-explanation", body: "  " },
  ];
  fs.writeFileSync(topicPath, `${JSON.stringify(emptyExplanationTopic, null, 2)}\n`);

  const emptyExplanationResult = runValidator();
  assert.equal(emptyExplanationResult.status, 1, "compare scenes without explanatory content must fail");
  assert.match(
    emptyExplanationResult.stderr,
    /animal-classification-tree compare-split scene must expose explanatory content/,
  );

  console.log("content alignment validation regression checks passed");
} finally {
  fs.rmSync(fixtureRoot, { recursive: true, force: true });
}
