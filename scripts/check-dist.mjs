import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const distDir = path.join(root, "dist");
const channel = process.env.VITE_CHANNEL || process.env.CHANNEL || "web-production";
const errors = [];

function requireFile(relativePath) {
  if (!fs.existsSync(path.join(distDir, relativePath))) {
    errors.push(`Missing dist file: ${relativePath}`);
  }
}

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(fullPath) : [fullPath];
  });
}

function readText(file) {
  try {
    return fs.readFileSync(file, "utf8");
  } catch {
    return "";
  }
}

requireFile("index.html");
requireFile("boards/kids-world/index.html");
requireFile("shared/icons/favicon.ico");
requireFile("shared/icons/og-image.jpg");
requireFile("release-manifest.json");

if (channel !== "web-production") {
  requireFile("boards/paw-patrol/index.html");
  requireFile("boards/spider-verse/index.html");
}

const files = walk(distDir);
const textFiles = files.filter((file) => /\.(html|js|css|json|txt|svg|map)$/i.test(file));
const forbiddenPatterns = [
  { pattern: "118.145.242.99", label: "legacy IP address" },
  { pattern: "__SITE_URL__", label: "unreplaced site URL placeholder" },
  { pattern: "__SITE_TITLE__", label: "unreplaced title placeholder" },
  { pattern: "__SITE_DESCRIPTION__", label: "unreplaced description placeholder" },
  { pattern: "__OG_IMAGE__", label: "unreplaced OG image placeholder" },
  { pattern: "localhost", label: "localhost reference" },
  { pattern: "127.0.0.1", label: "loopback reference" }
];

for (const file of textFiles) {
  const text = readText(file);
  for (const { pattern, label } of forbiddenPatterns) {
    if (text.includes(pattern)) {
      errors.push(`${path.relative(root, file)} contains ${label}`);
    }
  }
  const insecureExternal = text.match(/http:\/\/(?!www\.w3\.org\/)/);
  if (insecureExternal) {
    errors.push(`${path.relative(root, file)} contains an insecure external http:// URL`);
  }
}

for (const file of textFiles.filter((filePath) => filePath.endsWith(".html"))) {
  const text = readText(file);
  const ogMatches = [...text.matchAll(/<meta\s+property=["']og:image["']\s+content=["']([^"']+)["']/gi)];
  if (ogMatches.length === 0) {
    errors.push(`${path.relative(root, file)} is missing og:image`);
  }
  for (const match of ogMatches) {
    if (!match[1].startsWith("https://")) {
      errors.push(`${path.relative(root, file)} has non-https og:image: ${match[1]}`);
    }
  }
}

if (channel === "web-production") {
  const indexHtml = readText(path.join(distDir, "index.html"));
  if (indexHtml.includes("paw-patrol") || indexHtml.includes("spider-verse")) {
    errors.push("production dist/index.html exposes hidden board links");
  }
  for (const board of ["paw-patrol", "spider-verse"]) {
    if (fs.existsSync(path.join(distDir, "boards", board))) {
      errors.push(`production dist publishes hidden board directory: boards/${board}`);
    }
  }
}

if (errors.length > 0) {
  console.error("dist check failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(`dist check passed for ${channel}: ${files.length} files`);
