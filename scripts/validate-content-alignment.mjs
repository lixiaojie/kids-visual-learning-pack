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

function withoutQuotes(source) {
  return source.replace(/(["'`]).*?\1/g, "");
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
if (/\b(fs|path)\b/.test(withoutQuotes(packageSource))) {
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

const miniprogramConfigPath = path.join(root, "apps/miniprogram/config/index.ts");
const miniprogramConfig = fs.readFileSync(miniprogramConfigPath, "utf8");
if (miniprogramConfig.includes("apps/miniprogram/src/lib/kids-content")) {
  errors.push("apps/miniprogram must not alias @yutou/kids-content to an app-local adapter");
}

const miniprogramTopicPagePath = path.join(root, "apps/miniprogram/src/pages/topic/index.tsx");
const miniprogramTopicPage = fs.readFileSync(miniprogramTopicPagePath, "utf8");
const comparePairCardPath = path.join(root, "apps/miniprogram/src/components/topic/ComparePairCard.tsx");
const comparePairCardSource = fs.existsSync(comparePairCardPath) ? fs.readFileSync(comparePairCardPath, "utf8") : "";
if (!miniprogramTopicPage.includes("ComparePairCard")) {
  errors.push("miniprogram topic page must render comparePairs with ComparePairCard");
}
for (const requiredCompareField of ["pair.a.name", "pair.a.points", "pair.b.name", "pair.b.points", "pair.childConclusion"]) {
  if (!comparePairCardSource.includes(requiredCompareField)) {
    errors.push(`ComparePairCard must render ${requiredCompareField}`);
  }
}
for (const slug of renderReadySlugs) {
  const topic = readJson(`boards/kids-world/src/data/topics/${slug}.json`);
  if ((topic.comparePairs ?? []).some((pair) => pair.a?.points?.length > 0 || pair.b?.points?.length > 0)) {
    if (!miniprogramTopicPage.includes("ComparePairCard")) {
      errors.push(`${slug} has compare pair points but miniprogram does not render ComparePairCard`);
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
