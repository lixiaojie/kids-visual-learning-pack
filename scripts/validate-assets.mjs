import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join } from "node:path";

const MANIFEST_PATH = "boards/kids-world/src/data/image-generation-manifest.json";
const TOPICS_DIR = "boards/kids-world/src/data/topics";
const ASSETS_ROOT = "boards/kids-world/public/assets";

const manifest = JSON.parse(readFileSync(MANIFEST_PATH, "utf-8"));
let missing = 0;
let checked = 0;

console.log("=== Image Manifest ===");
for (const asset of manifest.assets || []) {
  checked++;
  const webpExists = asset.webpPath && existsSync(join("boards/kids-world/public", asset.webpPath));
  const pngExists = asset.pngPath && existsSync(join("boards/kids-world/public", asset.pngPath));

  if (!webpExists && !pngExists) {
    console.log(`❌ ${asset.assetId}: neither WebP nor PNG found`);
    console.log(`   webp: ${asset.webpPath || "(none)"}`);
    console.log(`   png:  ${asset.pngPath || "(none)"}`);
    missing++;
  } else if (!webpExists) {
    console.log(`⚠️  ${asset.assetId}: WebP missing (PNG exists)`);
    missing++;
  }
}

console.log(`\n=== Topic Asset References ===`);
const topicFiles = readdirSync(TOPICS_DIR).filter((f) => f.endsWith(".json"));
for (const file of topicFiles) {
  const topic = JSON.parse(readFileSync(join(TOPICS_DIR, file), "utf-8"));
  if (!topic.assets) continue;

  for (const [key, asset] of Object.entries(topic.assets)) {
    if (!asset.path) continue;
    checked++;
    const fullPath = join("boards/kids-world/public", asset.path);
    if (!existsSync(fullPath)) {
      console.log(`❌ ${file} → assets.${key}: ${asset.path} not found`);
      missing++;
    }
  }
}

console.log(`\n${checked} assets checked, ${missing} missing`);
if (missing > 0) {
  console.log(`\nNote: missing assets are expected during development. Run with --strict to fail on missing.`);
  if (process.argv.includes("--strict")) process.exit(1);
}
