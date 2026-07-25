import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const errors = [];

function readJson(relativePath) {
  return JSON.parse(fs.readFileSync(path.join(root, relativePath), "utf8"));
}

function listFiles(dir, predicate = () => true) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) return listFiles(fullPath, predicate);
    return predicate(fullPath) ? [fullPath] : [];
  });
}

function relative(filePath) {
  return path.relative(root, filePath);
}

function withoutCodeComments(source) {
  return source.replace(/\/\*[\s\S]*?\*\/|\/\/[^\n]*/g, "");
}

function withoutStringLiterals(source) {
  let result = "";
  let quote = null;
  let escaped = false;

  for (const character of source) {
    if (quote) {
      if (escaped) {
        escaped = false;
      } else if (character === "\\") {
        escaped = true;
      } else if (character === quote) {
        quote = null;
      }
      result += character === "\n" ? "\n" : " ";
      continue;
    }

    if (character === '"' || character === "'" || character === "`") {
      quote = character;
      result += " ";
      continue;
    }

    result += character;
  }

  return result;
}

const topicRegistry = readJson("boards/kids-world/src/data/topic-registry.json");
const channelPolicy = readJson("channel-policy.json");
const imageManifest = readJson("boards/kids-world/src/data/image-generation-manifest.json");

const renderReadySlugs = topicRegistry.topics
  .filter((topic) => topic.status === "render-ready" || topic.contentStatus === "render-ready")
  .map((topic) => topic.slug)
  .sort();
const miniprogramVisibleTopics = channelPolicy.miniprogram.visibleTopics;

if (!Array.isArray(miniprogramVisibleTopics)) {
  errors.push("channel-policy.json miniprogram.visibleTopics must be an explicit topic list");
} else {
  const visible = [...miniprogramVisibleTopics].sort();
  const missing = renderReadySlugs.filter((slug) => !visible.includes(slug));
  const extra = visible.filter((slug) => !renderReadySlugs.includes(slug));
  if (missing.length > 0) {
    errors.push(`miniprogram.visibleTopics is missing render-ready topics: ${missing.join(", ")}`);
  }
  if (extra.length > 0) {
    errors.push(`miniprogram.visibleTopics includes non-render-ready topics: ${extra.join(", ")}`);
  }
}

const topicFiles = new Set(
  listFiles(path.join(root, "boards/kids-world/src/data/topics"), (file) => file.endsWith(".json")).map((file) =>
    path.basename(file, ".json"),
  ),
);
for (const slug of renderReadySlugs) {
  if (!topicFiles.has(slug)) {
    errors.push(`render-ready topic has no topic JSON file: ${slug}`);
  }
}

const packageFiles = listFiles(path.join(root, "packages/kids-content/src"), (file) => file.endsWith(".ts"));
const packageSource = packageFiles.map((file) => fs.readFileSync(file, "utf8")).join("\n");
const forbiddenPackageImports = [
  "boards/kids-world/src/data/loaders/",
  "boards/kids-world/src/lib/asset-map",
  "boards/kids-world/src/pages/",
  "boards/kids-world/src/components/",
  "boards/kids-world/src/App",
  "boards/kids-world/src/main",
];
for (const forbidden of forbiddenPackageImports) {
  if (packageSource.includes(forbidden)) {
    errors.push(`packages/kids-content imports Web runtime or loader code: ${forbidden}`);
  }
}
if (/(from\s+["'](?:node:)?(?:fs|path)["']|require\(["'](?:node:)?(?:fs|path)["']\))/.test(packageSource)) {
  errors.push("packages/kids-content must not use Node-only fs/path APIs at runtime");
}
for (const slug of renderReadySlugs) {
  if (!packageSource.includes(`"${slug}"`) && !packageSource.includes(`${slug}:`)) {
    errors.push(`packages/kids-content import map is missing render-ready topic: ${slug}`);
  }
}

const webFiles = listFiles(path.join(root, "boards/kids-world/src"), (file) => /\.(ts|tsx)$/.test(file)).filter(
  (file) => !relative(file).startsWith("boards/kids-world/src/data/loaders/"),
);
for (const file of webFiles) {
  const source = fs.readFileSync(file, "utf8");
  if (source.includes("/data/loaders/") || source.includes("../data/loaders/") || source.includes("./data/loaders/")) {
    errors.push(`${relative(file)} must use @yutou/kids-content instead of data/loaders`);
  }
  if (
    relative(file) !== "boards/kids-world/src/lib/asset-map.ts" &&
    (source.includes("/lib/asset-map") || source.includes("../lib/asset-map") || source.includes("../../lib/asset-map"))
  ) {
    errors.push(`${relative(file)} must use @yutou/kids-content instead of lib/asset-map`);
  }
}

const topbarPath = path.join(root, "boards/kids-world/src/components/layout/Topbar.tsx");
const topbarSource = fs.readFileSync(topbarPath, "utf8");
for (const forbidden of ["getTopic(", "getTopicHref", "topicCards", "topic-nav"]) {
  if (topbarSource.includes(forbidden)) {
    errors.push(`Topbar must use stable global navigation, not topic-derived links: ${forbidden}`);
  }
}
for (const required of ["探索首页", "全部世界", "家长说明", "global-nav"]) {
  if (!topbarSource.includes(required)) {
    errors.push(`Topbar global navigation is missing ${required}`);
  }
}

const homePagePath = path.join(root, "boards/kids-world/src/pages/HomePage.tsx");
const homePageSource = fs.readFileSync(homePagePath, "utf8");
if (homePageSource.includes("InterestBand")) {
  errors.push("HomePage must not render the story interest entrance band");
}
if (!homePageSource.includes("FeaturedObservation")) {
  errors.push("HomePage must render the recent observation entry");
}
if (fs.existsSync(path.join(root, "boards/kids-world/src/components/home/InterestBand.tsx"))) {
  errors.push("Story interest entrance component must be removed from home components");
}

const sceneDeckContracts = [
  {
    label: "Web",
    entryPaths: ["boards/kids-world/src/pages/TopicPage.tsx"],
    componentPath: "boards/kids-world/src/components/topic/SceneDeckTopicPage.tsx",
  },
  {
    label: "miniprogram",
    entryPaths: [
      "apps/miniprogram/src/pages/topic/index.tsx",
      "apps/miniprogram/src/components/topic/TopicRuntimePage.tsx",
    ],
    componentPath: "apps/miniprogram/src/components/topic/SceneDeckTopicPage.tsx",
  },
];
const requiredSceneRuntimeTokens = [
  "normalizeTopicToSceneDeck",
  "createInitialSceneInteractionState",
  "reduceSceneInteractionState",
  "resolveScenePresentation",
];
const requiredSceneUiTokens = [
  "deck.scenes.map",
  'type: "SELECT_SCENE"',
  "activeScene.focusItems.map",
  'type: "SELECT_FOCUS"',
  "presentation.activeEvidence",
  "activeScene.visual.regions.map",
  "activeScene.contentBlocks.map",
  "activeScene.tasks.map",
  "task.options.map",
  'type: "CLICK_TASK_OPTION"',
  "taskState?.feedbackMessage",
];
for (const contract of sceneDeckContracts) {
  for (const entryPath of contract.entryPaths) {
    const entrySource = withoutCodeComments(fs.readFileSync(path.join(root, entryPath), "utf8"));
    const importsSceneDeck =
      /import\s+\{\s*SceneDeckTopicPage\s*\}\s+from\s+["'][^"']*SceneDeckTopicPage["']/.test(entrySource);
    const rendersSceneDeck = /<SceneDeckTopicPage(?:\s|\/|>)/.test(
      withoutStringLiterals(entrySource),
    );
    if (!importsSceneDeck || !rendersSceneDeck) {
      errors.push(`${contract.label} topic runtime must render SceneDeckTopicPage: ${entryPath}`);
    }
  }

  const componentSource = withoutCodeComments(
    fs.readFileSync(path.join(root, contract.componentPath), "utf8"),
  );
  if (!/export\s+function\s+SceneDeckTopicPage\s*\(/.test(componentSource)) {
    errors.push(`${contract.label} scene deck must export SceneDeckTopicPage`);
  }
  for (const required of requiredSceneRuntimeTokens) {
    if (!new RegExp(`\\b${required}\\s*\\(`).test(componentSource)) {
      errors.push(`${contract.label} scene deck must call ${required}`);
    }
  }
  for (const required of requiredSceneUiTokens) {
    if (!componentSource.includes(required)) {
      errors.push(`${contract.label} scene deck must wire ${required}`);
    }
  }
}

const miniprogramConfigPath = path.join(root, "apps/miniprogram/config/index.ts");
const miniprogramConfig = fs.readFileSync(miniprogramConfigPath, "utf8");
if (miniprogramConfig.includes("apps/miniprogram/src/lib/kids-content")) {
  errors.push("apps/miniprogram must not alias @yutou/kids-content to an app-local adapter");
}

for (const slug of renderReadySlugs) {
  const topic = readJson(`boards/kids-world/src/data/topics/${slug}.json`);
  if ((topic.comparePairs ?? []).some((pair) => pair.a?.points?.length > 0 || pair.b?.points?.length > 0)) {
    const compareScene = topic.learningScenes?.find((scene) => scene.sceneType === "compare-split");
    if (!compareScene) {
      errors.push(`${slug} has compare evidence but no compare-split learning scene`);
      continue;
    }

    const compareSources = new Set(
      topic.comparePairs.map((pair) => `comparePairs.${pair.id}`),
    );
    if (!compareScene.focusItems?.some((focus) => compareSources.has(focus.source))) {
      errors.push(`${slug} compare-split scene must focus comparePairs evidence`);
    }
    const hasExplanatoryContent = compareScene.contentBlocks?.some((block) =>
      Boolean(block.body?.trim() || block.items?.some((item) => item.trim()))
    );
    if (!hasExplanatoryContent) {
      errors.push(`${slug} compare-split scene must expose explanatory content`);
    }
  }
}

const localAdapterPath = path.join(root, "apps/miniprogram/src/lib/kids-content.ts");
if (fs.existsSync(localAdapterPath)) {
  const adapterSource = fs.readFileSync(localAdapterPath, "utf8").trim();
  const pureReExport = /^export\s+\*\s+from\s+["']@yutou\/kids-content["'];?$/.test(adapterSource);
  if (!pureReExport) {
    errors.push("apps/miniprogram/src/lib/kids-content.ts must be removed or reduced to a pure re-export");
  }
}

const manifestAssetIds = new Set(imageManifest.assets.map((asset) => asset.assetId));
const manifestWebpPaths = new Set(imageManifest.assets.map((asset) => asset.webpPath).filter(Boolean));
const packageAssetIds = [...packageSource.matchAll(/:\s*"([^"]+)"/g)]
  .map((match) => match[1])
  .filter((value) => value.includes("-hero") || value.includes("-card"));
for (const assetId of packageAssetIds) {
  if (!manifestAssetIds.has(assetId)) {
    errors.push(`packages/kids-content references generated asset id missing from manifest: ${assetId}`);
  }
}
for (const slug of renderReadySlugs) {
  const topic = readJson(`boards/kids-world/src/data/topics/${slug}.json`);
  const visualSlots = topic.visualSlots ?? [];
  const visualEvidenceBindings = topic.visualEvidenceBindings ?? [];
  const assetCount = Object.keys(topic.assets ?? {}).length;

  if (assetCount > 1 && visualSlots.length <= 1) {
    errors.push(`${slug} has ${assetCount} topic assets but does not bind module-level visualSlots`);
  }

  if (visualSlots.length > 0 && !visualSlots.some((slot) => slot.target === "hero")) {
    errors.push(`${slug} visualSlots must include a hero target`);
  }

  if (visualEvidenceBindings.length === 0) {
    errors.push(`${slug} must define visualEvidenceBindings for interactive evidence coverage`);
  }

  for (const slot of visualSlots) {
    if (!manifestAssetIds.has(slot.assetId)) {
      errors.push(`${slug} visualSlot "${slot.id}" references missing manifest assetId: ${slot.assetId}`);
    }
  }

  for (const [name, asset] of Object.entries(topic.assets ?? {})) {
    if (asset?.path && !manifestWebpPaths.has(asset.path)) {
      errors.push(`${slug} asset "${name}" is missing from image-generation-manifest.json: ${asset.path}`);
    }
  }
}

if (errors.length > 0) {
  console.error("content alignment validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(
  `content alignment checked: ${renderReadySlugs.length} render-ready topics, ${packageFiles.length} package files`,
);
