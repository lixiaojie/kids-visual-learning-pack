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
  "src/components/topic/SceneDeckTopicPage.tsx",
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
const sceneDeckComponent = fs.readFileSync(path.join(appDir, "src/components/topic/SceneDeckTopicPage.tsx"), "utf8");

if (!indexPage.includes("@yutou/kids-content")) {
  errors.push("index page must use @yutou/kids-content");
}
if (indexPage.includes("slice(0, 6)")) {
  errors.push("index page must not truncate the miniprogram visible topic list");
}
if (!topicPage.includes("useShareAppMessage") || !topicPage.includes("useShareTimeline")) {
  errors.push("topic page must define friend and timeline share handlers");
}
if (!topicPage.includes("SceneDeckTopicPage")) {
  errors.push("topic page must render SceneDeckTopicPage");
}
for (const requiredSceneDeckWire of [
  "normalizeTopicToSceneDeck",
  "createInitialSceneInteractionState",
  "reduceSceneInteractionState",
  "resolveScenePresentation",
  "SELECT_SCENE",
  "SELECT_FOCUS",
  "CLICK_TASK_OPTION",
  "activeEvidence",
  "GeneratedImage",
  "scene-region",
  "scene-task-feedback",
]) {
  if (!sceneDeckComponent.includes(requiredSceneDeckWire)) {
    errors.push(`SceneDeckTopicPage must wire scene deck feature: ${requiredSceneDeckWire}`);
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
if (!imageComponent.includes("load = false")) {
  errors.push("GeneratedImage must not request remote CDN assets by default in the miniprogram");
}

if (errors.length > 0) {
  console.error("miniprogram scaffold validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`miniprogram scaffold checked: ${requiredFiles.length} files`);
