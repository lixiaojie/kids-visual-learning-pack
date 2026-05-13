import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { execFileSync } from "node:child_process";

const root = process.cwd();
const distDir = path.join(root, "dist");
const config = JSON.parse(fs.readFileSync(path.join(root, "site.config.json"), "utf8"));
const siteUrl = (process.env.SITE_URL || config.siteUrl).replace(/\/+$/, "");
const ogImage = new URL(config.ogImage, `${siteUrl}/`).toString();
const channel = process.env.VITE_CHANNEL || process.env.CHANNEL || "web-production";

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(fullPath) : [fullPath];
  });
}

function replaceOrInsertMeta(html, property, value) {
  const pattern = new RegExp(`<meta\\s+property=["']${property}["']\\s+content=["'][^"']*["']\\s*/?>`, "i");
  const tag = `<meta property="${property}" content="${value}">`;
  if (pattern.test(html)) {
    return html.replace(pattern, tag);
  }
  return html.replace("</head>", `  ${tag}\n</head>`);
}

function replaceOrInsertNameMeta(html, name, value) {
  const pattern = new RegExp(`<meta\\s+name=["']${name}["']\\s+content=["'][^"']*["']\\s*/?>`, "i");
  const tag = `<meta name="${name}" content="${value}">`;
  if (pattern.test(html)) {
    return html.replace(pattern, tag);
  }
  return html.replace("</head>", `  ${tag}\n</head>`);
}

for (const file of walk(distDir).filter((filePath) => filePath.endsWith(".html"))) {
  let html = fs.readFileSync(file, "utf8");
  html = html
    .replaceAll("https://118.145.242.99/kids/shared/icons/og-image.jpg", "__OG_IMAGE__")
    .replaceAll("__SITE_URL__", siteUrl)
    .replaceAll("__SITE_TITLE__", config.defaultTitle)
    .replaceAll("__SITE_DESCRIPTION__", config.defaultDescription)
    .replaceAll("__OG_IMAGE__", ogImage);
  html = replaceOrInsertMeta(html, "og:image", ogImage);
  html = replaceOrInsertMeta(html, "og:type", "website");
  html = replaceOrInsertNameMeta(html, "description", config.defaultDescription);
  fs.writeFileSync(file, html);
}

let commit = "unknown";
try {
  commit = execFileSync("git", ["rev-parse", "--short", "HEAD"], { cwd: root, encoding: "utf8" }).trim();
} catch {
  // Keep the build deterministic in environments without Git metadata.
}

const topicRegistry = JSON.parse(
  fs.readFileSync(path.join(root, "boards/kids-world/src/data/topic-registry.json"), "utf8"),
);
const imageManifest = JSON.parse(
  fs.readFileSync(path.join(root, "boards/kids-world/src/data/image-generation-manifest.json"), "utf8"),
);
const renderReadyTopics = topicRegistry.topics.filter(
  (topic) => topic.status === "render-ready" || topic.contentStatus === "render-ready",
);

fs.writeFileSync(
  path.join(distDir, "release-manifest.json"),
  `${JSON.stringify(
    {
      version: new Date().toISOString().slice(0, 10).replaceAll("-", "."),
      commit,
      channel,
      topics: renderReadyTopics.length,
      assets: imageManifest.assets.length,
      deployedAt: new Date().toISOString(),
    },
    null,
    2,
  )}\n`,
);

console.log(`Site meta generated for ${siteUrl} (${channel})`);
