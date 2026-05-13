import { mkdirSync, writeFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";

const sourcePath = process.argv[2];

if (!sourcePath) {
  console.error("Usage: node scripts/import-kids-world-image-prompts.mjs <prompt-package.md>");
  process.exit(1);
}

const markdown = await import("node:fs").then(({ readFileSync }) => readFileSync(sourcePath, "utf8"));

function extractCodeBlockBetween(startHeading, endHeading) {
  const start = markdown.indexOf(startHeading);
  const end = markdown.indexOf(endHeading, start + startHeading.length);
  const slice = markdown.slice(start, end);
  const match = slice.match(/```text\n([\s\S]*?)\n```/);
  if (!match) {
    throw new Error(`Could not find code block for ${startHeading}`);
  }
  return match[1].trim();
}

const commonPrefix = extractCodeBlockBetween("# 1. 通用前缀", "# 2. 通用后缀");
const commonSuffix = extractCodeBlockBetween("# 2. 通用后缀", "# 3. 分类型规则");

const assetBlockPattern =
  /^##\s+([\d.]+)\s+(.+?)\n\n- assetId: `([^`]+)`\n- 文件名：`([^`]+)`\n- 推荐比例：([^\n]+)\n\n```text\n([\s\S]*?)\n```/gm;

const firstBatchIds = new Set([
  "homepage-exploration-map-hero",
  "life-animal-classification-tree-hero",
  "body-blood-cells-3d-hero",
  "space-solar-system-overview-hero",
  "earth-climate-cities-hero",
  "human-made-llm-kids-basics-hero",
]);

function inferFolder(assetId, filename) {
  if (assetId.startsWith("homepage-")) return "shared/homepage";
  if (assetId.startsWith("shared-")) return "shared/ui";
  if (assetId.startsWith("animation-")) return "animation";
  if (filename.startsWith("life-insects-and-spiders-")) return "life/insects-and-spiders";
  if (filename.startsWith("life-animal-classification-tree-")) return "life/animal-classification-tree";
  if (filename.startsWith("body-blood-cells-")) return "body/blood-cells-3d";
  if (filename.startsWith("space-solar-system-")) return "space/solar-system-overview";
  if (filename.startsWith("earth-climate-")) return "earth/earth-climate-cities";
  if (filename.startsWith("human-made-llm-")) return "human-made/llm-kids-basics";
  throw new Error(`No asset folder mapping for ${assetId} (${filename})`);
}

function inferSize(ratio, assetId) {
  if (assetId === "homepage-exploration-map-hero") return "2048x1152";
  if (assetId === "shared-ui-completion-glow") return "2048x1152";
  if (ratio.includes("1:1")) return "1024x1024";
  if (ratio.includes("4:3") && !ratio.includes("16:9")) return "1536x1152";
  return "2048x1152";
}

function inferUseCase(assetId) {
  if (assetId.includes("icons") || assetId.includes("badge") || assetId.includes("status") || assetId.includes("ui-")) {
    return "scientific-educational";
  }
  if (assetId.includes("mechanism") || assetId.includes("compare") || assetId.includes("flow") || assetId.includes("sequence")) {
    return "infographic-diagram";
  }
  return "illustration-story";
}

const assets = [];
let match;
let batchOrder = 1;

while ((match = assetBlockPattern.exec(markdown))) {
  const [, section, title, assetId, filename, ratio, body] = match;
  const folder = inferFolder(assetId, filename);
  const webpFilename = filename.replace(/\.png$/i, ".webp");
  const prompt = `${commonPrefix}\n\n${body.trim()}\n\n${commonSuffix}`;

  assets.push({
    batchOrder: batchOrder++,
    phase: firstBatchIds.has(assetId) ? "style-validation" : "full-production",
    section,
    title: title.trim(),
    assetId,
    filename,
    webpFilename,
    ratio: ratio.trim(),
    size: inferSize(ratio, assetId),
    useCase: inferUseCase(assetId),
    pngPath: `/assets/${folder}/${filename}`,
    webpPath: `/assets/${folder}/${webpFilename}`,
    sourceFile: `boards/kids-world/public/assets/${folder}/${filename}`,
    deploymentFile: `boards/kids-world/public/assets/${folder}/${webpFilename}`,
    prompt,
  });
}

if (assets.length < 40) {
  throw new Error(`Expected the full V2.1 prompt package; parsed only ${assets.length} assets.`);
}

const manifest = {
  project: "芋头宇宙",
  version: "2.1",
  sourcePromptPackage: basename(sourcePath),
  generatedAt: new Date().toISOString(),
  notes: [
    "PNG is the source/original generation output.",
    "WebP is the deployment/browser output.",
    "The app keeps CSS placeholders visible until image files are present.",
  ],
  assets,
};

mkdirSync("boards/kids-world/src/data", { recursive: true });
mkdirSync("tmp/imagegen", { recursive: true });

writeFileSync("boards/kids-world/src/data/image-generation-manifest.json", `${JSON.stringify(manifest, null, 2)}\n`);

const jsonl = assets
  .map((asset) =>
    JSON.stringify({
      asset_id: asset.assetId,
      prompt: asset.prompt,
      use_case: asset.useCase,
      size: asset.size,
      quality: "medium",
      output_format: "png",
      out: asset.filename,
    }),
  )
  .join("\n");

writeFileSync("tmp/imagegen/kids-world-v2.1-prompts.jsonl", `${jsonl}\n`);

for (const asset of assets) {
  mkdirSync(dirname(asset.sourceFile), { recursive: true });
}

console.log(`Imported ${assets.length} image prompts.`);
console.log("Wrote boards/kids-world/src/data/image-generation-manifest.json");
console.log("Wrote tmp/imagegen/kids-world-v2.1-prompts.jsonl");
