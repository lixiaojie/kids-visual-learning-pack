import { existsSync, readFileSync } from "node:fs";
import { strict as assert } from "node:assert";

const root = new URL("./", import.meta.url);
const readJson = (path) => JSON.parse(readFileSync(new URL(path, root), "utf8"));
const html = readFileSync(new URL("./index.html", root), "utf8");
const styles = readFileSync(new URL("./src/styles.css", root), "utf8");

const explorationMap = readJson("./src/data/exploration-map.json");
const imageManifest = readJson("./src/data/image-generation-manifest.json");
const registry = readJson("./src/data/topic-registry.json");
const i18n = readJson("./src/data/i18n-config.json");
const enHome = readJson("./src/data/locales/en-US/exploration-map.json");

const topicSlugs = [
  "insects-and-spiders",
  "animal-classification-tree",
  "blood-cells-3d",
  "solar-system-overview",
  "earth-climate-cities",
  "llm-kids-basics",
];

assert.equal(explorationMap.title, "芋头世界");
assert.equal(explorationMap.worlds[0].id, "animation");
assert.equal(explorationMap.worlds.length, 7);
assert.equal(explorationMap.worlds[0].topicCards[0].href, "boards/spider-verse/index.html");
assert.equal(explorationMap.worlds[0].topicCards[1].href, "boards/paw-patrol/index.html");
assert.deepEqual(i18n.supportedLocales.map((item) => item.locale), ["zh-CN", "en-US"]);
assert.equal(enHome.statusLegend[0].status, "completed");
assert.equal(enHome.worlds[0].topicCards[0].cardDescription.includes("growth"), true);
assert.equal(registry.topics.length, 6);
assert.equal(imageManifest.project, "芋头世界");
assert.equal(imageManifest.version, "2.1");
assert.ok(imageManifest.assets.length >= 40, "Image prompt manifest should include the full batch asset list");
assert.ok(
  imageManifest.assets.every((asset) => asset.pngPath.endsWith(".png") && asset.webpPath.endsWith(".webp")),
  "Each generated image asset should define PNG source and WebP deployment paths",
);
assert.ok(
  imageManifest.assets.some((asset) => asset.assetId === "homepage-exploration-map-hero"),
  "Image prompt manifest should include the homepage hero",
);
assert.ok(
  existsSync(new URL("../../tmp/imagegen/kids-world-v2.1-prompts.jsonl", root)),
  "Batch image generation JSONL handoff should exist",
);
assert.ok(
  existsSync(new URL("../../docs/kids-world-image-generation-handoff.md", root)),
  "Image generation handoff doc should exist",
);

for (const slug of topicSlugs) {
  const topic = readJson(`./src/data/topics/${slug}.json`);
  const overlayPath = `./src/data/locales/en-US/topics/${slug}.json`;
  const overlay = readJson(overlayPath);

  assert.equal(topic.slug, slug);
  assert.equal(overlay.slug, slug);
  assert.ok(topic.hero, `${slug} should define hero content`);
  assert.ok(topic.classificationGroups?.length >= 3, `${slug} should define classification groups`);
  assert.ok(topic.representativeObjects?.length >= 4, `${slug} should define representative objects`);
  assert.ok(topic.clickTasks?.length >= 4, `${slug} should define click tasks`);
  assert.deepEqual(
    overlay.clickTasks.map((task) => task.id),
    topic.clickTasks.map((task) => task.id),
    `${slug} overlay must preserve task ids`,
  );
}

assert.ok(existsSync(new URL("./src/App.tsx", root)));
assert.ok(existsSync(new URL("./src/styles.css", root)));
assert.ok(html.includes('name="viewport"'), "Page should define a mobile viewport");
assert.ok(styles.includes("@media (max-width: 640px)"), "Styles should include a phone breakpoint");
assert.ok(styles.includes(".mobile-menu-button"), "Header should expose a mobile navigation control");
assert.ok(styles.includes(".topbar nav.open"), "Mobile navigation should have an open state");
assert.ok(styles.includes("grid-template-columns: 1fr"), "Mobile layout should collapse dense grids to one column");
assert.ok(appIncludes("image-generation-manifest.json"), "App should consume the image generation manifest");
assert.ok(appIncludes("resolveBoardAsset"), "App should resolve board-local asset URLs for subpath deployment");
assert.ok(appIncludes("boards/kids-world/public"), "App should resolve generated images during root dev-server previews");
assert.ok(appIncludes("onError"), "App should gracefully fall back when generated assets are not present yet");
assert.ok(appIncludes("home-hero-image"), "Home hero should render the generated homepage image");
assert.ok(appIncludes("topic-card-image"), "Topic cards should render generated card images when available");
assert.ok(appIncludes("generated-scene"), "Topic scene placeholder should switch to generated-image presentation");

console.log("Kids-world board structure checks passed");

function appIncludes(fragment) {
  return readFileSync(new URL("./src/App.tsx", root), "utf8").includes(fragment);
}
