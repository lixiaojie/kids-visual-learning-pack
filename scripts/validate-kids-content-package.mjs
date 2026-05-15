import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const packageDir = path.join(root, "packages/kids-content");
const requiredFiles = [
  "package.json",
  "tsconfig.json",
  "src/index.ts",
  "src/assets.ts",
  "src/evidence.ts",
  "src/map.ts",
  "src/media.ts",
  "src/merge.ts",
  "src/topics.ts",
];
const requiredExports = [
  "getTopic",
  "hasTopicData",
  "getMap",
  "getVisibleTopicSlugs",
  "getKnowledgeTopicAssetId",
  "getCdnAssetUrl",
  "getGeneratedImageUrl",
  "ContentChannel",
  "Topic",
  "Locale",
  "ExplorationMap",
  "resolveVisualEvidence",
  "getTopicEvidenceCoverage",
  "VisualEvidenceState",
  "VisualEvidenceBinding",
];
const errors = [];

for (const file of requiredFiles) {
  if (!fs.existsSync(path.join(packageDir, file))) {
    errors.push(`Missing kids-content file: ${file}`);
  }
}

const indexPath = path.join(packageDir, "src/index.ts");
const indexSource = fs.existsSync(indexPath) ? fs.readFileSync(indexPath, "utf8") : "";
for (const exportedName of requiredExports) {
  if (!indexSource.includes(exportedName)) {
    errors.push(`packages/kids-content/src/index.ts does not export ${exportedName}`);
  }
}

if (errors.length > 0) {
  console.error("kids-content package validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`kids-content package checked: ${requiredFiles.length} files, ${requiredExports.length} exports`);
