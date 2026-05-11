import { copyFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";

const sourceDir = process.argv[2];

if (!sourceDir) {
  console.error("Usage: node scripts/import-kids-world-generated-images.mjs <flat-generated-png-dir>");
  process.exit(1);
}

const manifest = JSON.parse(readFileSync("boards/kids-world/src/data/image-generation-manifest.json", "utf8"));
const missing = [];
let copied = 0;

for (const asset of manifest.assets) {
  const source = join(sourceDir, asset.filename);
  if (!existsSync(source)) {
    missing.push(asset.filename);
    continue;
  }

  mkdirSync(dirname(asset.sourceFile), { recursive: true });
  copyFileSync(source, asset.sourceFile);
  copied += 1;
}

if (missing.length > 0) {
  console.error(`Copied ${copied} PNG files, but ${missing.length} files were missing:`);
  for (const filename of missing) {
    console.error(`- ${filename}`);
  }
  process.exit(1);
}

console.log(`Copied ${copied} generated PNG files into boards/kids-world/public/assets/.`);
