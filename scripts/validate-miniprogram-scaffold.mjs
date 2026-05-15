import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const appDir = path.join(root, "apps/miniprogram");
const requiredFiles = [
  "package.json",
  "babel.config.js",
  "project.config.json",
  "tsconfig.json",
  "config/index.ts",
  "config/prod.ts",
  "src/app.config.ts",
  "src/app.tsx",
  "src/app.scss",
  "src/pages/index/index.tsx",
  "src/pages/index/index.config.ts",
  "src/pages/topic/index.tsx",
  "src/pages/topic/index.config.ts",
  "src/pages/about/index.tsx",
  "src/pages/about/index.config.ts",
  "src/components/shared/GeneratedImage.tsx",
  "src/components/topic/ClickTaskCard.tsx",
  "src/components/topic/ClickTaskDeck.tsx",
  "src/components/topic/ComparePairCard.tsx",
  "src/components/topic/InfoList.tsx",
  "src/components/topic/LearningFlowRail.tsx",
  "src/components/topic/TopicVisual.tsx",
];
const errors = [];

for (const file of requiredFiles) {
  if (!fs.existsSync(path.join(appDir, file))) {
    errors.push(`Missing miniprogram file: ${file}`);
  }
}

const appConfigPath = path.join(appDir, "src/app.config.ts");
const appConfig = fs.existsSync(appConfigPath) ? fs.readFileSync(appConfigPath, "utf8") : "";
const taroConfigPath = path.join(appDir, "config/index.ts");
const taroConfig = fs.existsSync(taroConfigPath) ? fs.readFileSync(taroConfigPath, "utf8") : "";
for (const page of ["pages/index/index", "pages/topic/index", "pages/about/index"]) {
  if (!appConfig.includes(page)) {
    errors.push(`src/app.config.ts does not register ${page}`);
  }
}
if (taroConfig.includes("src/lib/kids-content") || taroConfig.includes("apps/miniprogram/src/lib/kids-content")) {
  errors.push("config/index.ts must not alias @yutou/kids-content to an app-local adapter");
}
if (fs.existsSync(path.join(appDir, "src/lib/kids-content.ts"))) {
  errors.push("src/lib/kids-content.ts must not contain a private content runtime");
}

const indexPage = fs.readFileSync(path.join(appDir, "src/pages/index/index.tsx"), "utf8");
const topicPage = fs.readFileSync(path.join(appDir, "src/pages/topic/index.tsx"), "utf8");
const aboutPage = fs.readFileSync(path.join(appDir, "src/pages/about/index.tsx"), "utf8");
const imageComponent = fs.readFileSync(path.join(appDir, "src/components/shared/GeneratedImage.tsx"), "utf8");
const clickTaskCard = fs.readFileSync(path.join(appDir, "src/components/topic/ClickTaskCard.tsx"), "utf8");
const clickTaskDeck = fs.readFileSync(path.join(appDir, "src/components/topic/ClickTaskDeck.tsx"), "utf8");
const topicVisual = fs.readFileSync(path.join(appDir, "src/components/topic/TopicVisual.tsx"), "utf8");
const interactionSource = fs.readFileSync(path.join(root, "packages/kids-content/src/interaction.ts"), "utf8");

if (!indexPage.includes("@yutou/kids-content")) {
  errors.push("index page must use @yutou/kids-content");
}
if (indexPage.includes("slice(0, 6)")) {
  errors.push("index page must not truncate the miniprogram visible topic list");
}
if (!topicPage.includes("useShareAppMessage") || !topicPage.includes("useShareTimeline")) {
  errors.push("topic page must define friend and timeline share handlers");
}
for (const requiredTaskSupport of [
  "singleChoice",
  "findTarget",
  "sequenceClick",
  "correctOptionId",
  "targetIds",
  "correctSequence",
  "wrongHints",
  "resolveTopicPresentation",
  "data-evidence-source",
]) {
  const supportSource = `${clickTaskCard}\n${clickTaskDeck}\n${topicPage}\n${interactionSource}`;
  if (!supportSource.includes(requiredTaskSupport)) {
    errors.push(`miniprogram controlled task flow must support ${requiredTaskSupport}`);
  }
}
for (const requiredTopicSection of ["ClickTaskDeck", "ComparePairCard", "representativeObjects", "comparePairs", "parentTips"]) {
  if (!topicPage.includes(requiredTopicSection)) {
    errors.push(`topic page must render ${requiredTopicSection}`);
  }
}
for (const requiredTopicSection of ["classificationGroups", "secondaryMechanism", "relatedTopics"]) {
  if (!topicPage.includes(requiredTopicSection)) {
    errors.push(`topic page must render ${requiredTopicSection} for section parity`);
  }
}
for (const requiredTopicFlow of ["LearningFlowRail", "TopicVisual", "getTopicLearningFlow", "getVisualSlotForTarget"]) {
  if (!topicPage.includes(requiredTopicFlow)) {
    errors.push(`topic page must support learning flow and visual slots: ${requiredTopicFlow}`);
  }
}
for (const requiredEvidenceWire of ["resolveTopicPresentation", "evidence={", "data-evidence-source"]) {
  if (!topicPage.includes(requiredEvidenceWire) && !clickTaskCard.includes(requiredEvidenceWire) && !clickTaskDeck.includes(requiredEvidenceWire) && !topicVisual.includes(requiredEvidenceWire)) {
    errors.push(`miniprogram topic UI must wire visual evidence: ${requiredEvidenceWire}`);
  }
}
for (const requiredEvidencePanel of ["evidence-panel", "evidenceTitle", "evidenceCopy", "markerChips"]) {
  if (!topicVisual.includes(requiredEvidencePanel)) {
    errors.push(`TopicVisual must render visual evidence panel field: ${requiredEvidencePanel}`);
  }
}
if (/\.slice\(\s*0\s*,/.test(topicPage)) {
  errors.push("topic page must not silently truncate topic sections with slice(0, n)");
}
if (!aboutPage.includes("不登录") || !aboutPage.includes("不收集儿童")) {
  errors.push("about page must state the no-login/no-child-data privacy posture");
}
if (!imageComponent.includes("getGeneratedImageUrl")) {
  errors.push("GeneratedImage must resolve CDN URLs through kids-content");
}

if (errors.length > 0) {
  console.error("miniprogram scaffold validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`miniprogram scaffold checked: ${requiredFiles.length} files`);
