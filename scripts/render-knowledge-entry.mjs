#!/usr/bin/env node
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import {
  assertLegacySlugSafe,
  loadKnowledgeEntry,
  renderHubHtml,
  renderLegacyTopicPageHtml,
  repoRoot,
  topicTitleBySlug,
} from "./knowledge-entry.mjs";

const args = new Set(process.argv.slice(2));
const root = repoRoot();
const entry = loadKnowledgeEntry(root);
const titles = topicTitleBySlug(root);

function takeOption(name) {
  const index = process.argv.indexOf(name);
  if (index === -1) return null;
  return process.argv[index + 1] ?? null;
}

if (args.has("--write-hub") || args.has("--check-hub")) {
  const html = renderHubHtml(entry);
  const hubPath = join(root, "index.html");
  if (args.has("--check-hub")) {
    const current = readFileSync(hubPath, "utf8");
    if (current !== html) {
      console.error("index.html drifted from shared/knowledge-entry.json; run:");
      console.error("  node scripts/render-knowledge-entry.mjs --write-hub");
      process.exit(1);
    }
    console.log("Knowledge hub matches activeMode=" + entry.activeMode);
  }
  if (args.has("--write-hub")) {
    writeFileSync(hubPath, html);
    console.log("Wrote index.html for activeMode=" + entry.activeMode);
  }
}

const legacyOut = takeOption("--legacy-out");
if (legacyOut) {
  const outRoot = isAbsolute(legacyOut) ? legacyOut : join(root, legacyOut);
  for (const slug of entry.frozenKidsWorldTopics) {
    assertLegacySlugSafe(slug);
    const title = titles.get(slug);
    if (!title) {
      throw new Error(`frozen slug missing from topic-registry.json: ${slug}`);
    }
    const dir = join(outRoot, slug);
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, "index.html"), renderLegacyTopicPageHtml(slug, title, entry));
  }
  console.log(`Wrote ${entry.frozenKidsWorldTopics.length} legacy topic pages under ${legacyOut}`);
}

if (!args.has("--write-hub") && !args.has("--check-hub") && !legacyOut) {
  console.error("Usage: node scripts/render-knowledge-entry.mjs [--write-hub] [--check-hub] [--legacy-out DIR]");
  process.exit(2);
}
