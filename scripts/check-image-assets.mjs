import { existsSync, readdirSync, statSync } from "node:fs";
import { extname, join, relative } from "node:path";

const root = process.cwd();
const boardsDir = join(root, "boards");
const checkedExtensions = new Set([".png", ".webp", ".jpg", ".jpeg"]);
const errors = [];
let checkedPairs = 0;

function walk(dir) {
  for (const entry of readdirSync(dir)) {
    if (entry === "node_modules" || entry === "dist" || entry === ".git") {
      continue;
    }

    const path = join(dir, entry);
    const stats = statSync(path);

    if (stats.isDirectory()) {
      walk(path);
      continue;
    }

    const relativePath = relative(root, path);

    if (!relativePath.split("/").includes("assets")) {
      continue;
    }

    const extension = extname(entry).toLowerCase();

    if (!checkedExtensions.has(extension)) {
      continue;
    }

    if (extension === ".jpg" || extension === ".jpeg") {
      errors.push(`${relativePath} should use the PNG source + WebP deployment pair policy.`);
      continue;
    }

    const counterpart = path.replace(/\.(png|webp)$/i, extension === ".png" ? ".webp" : ".png");

    if (!existsSync(counterpart)) {
      errors.push(`${relativePath} is missing ${relative(root, counterpart)}.`);
      continue;
    }

    checkedPairs += 1;
  }
}

walk(boardsDir);

if (errors.length > 0) {
  console.error("Image asset policy check failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`Image asset policy checks passed (${checkedPairs} paired files checked)`);
