import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const policyPath = path.join(root, "channel-policy.json");
const registryPath = path.join(root, "boards/kids-world/src/data/topic-registry.json");
const requiredDocPaths = [
  "docs/compliance/wechat-miniprogram-checklist.md",
  "docs/compliance/content-ip-risk-register.md",
];

const policy = JSON.parse(fs.readFileSync(policyPath, "utf8"));
const registry = JSON.parse(fs.readFileSync(registryPath, "utf8"));
const topics = registry.topics ?? [];
const topicsBySlug = new Map(topics.map((topic) => [topic.slug, topic]));
const renderReadySlugs = new Set(
  topics
    .filter((topic) => topic.status === "render-ready" || topic.contentStatus === "render-ready")
    .map((topic) => topic.slug),
);

const requiredChannels = ["web-production", "web-preview", "miniprogram"];
const errors = [];

for (const docPath of requiredDocPaths) {
  const absolutePath = path.join(root, docPath);
  if (!fs.existsSync(absolutePath)) {
    errors.push(`Missing compliance document: ${docPath}`);
    continue;
  }

  const text = fs.readFileSync(absolutePath, "utf8");
  if (!text.includes("小程序首版")) {
    errors.push(`${docPath}: must document 小程序首版 scope`);
  }
}

for (const channel of requiredChannels) {
  if (!policy[channel]) {
    errors.push(`Missing policy channel: ${channel}`);
  }
}

for (const [channel, channelPolicy] of Object.entries(policy)) {
  const visibleBoards = channelPolicy.visibleBoards ?? [];
  const hiddenBoards = channelPolicy.hiddenBoards ?? [];
  const overlap = visibleBoards.filter((board) => hiddenBoards.includes(board));
  if (overlap.length > 0) {
    errors.push(`${channel}: boards cannot be both visible and hidden: ${overlap.join(", ")}`);
  }
}

const miniprogram = policy.miniprogram;
if (miniprogram) {
  for (const board of ["paw-patrol", "spider-verse"]) {
    if ((miniprogram.visibleBoards ?? []).includes(board)) {
      errors.push(`miniprogram: ${board} must not be visible`);
    }
  }

  if (!Array.isArray(miniprogram.visibleTopics)) {
    errors.push("miniprogram: visibleTopics must be an explicit slug array");
  } else {
    for (const slug of miniprogram.visibleTopics) {
      const topic = topicsBySlug.get(slug);
      if (!topic) {
        errors.push(`miniprogram: unknown visible topic "${slug}"`);
        continue;
      }
      if (!renderReadySlugs.has(slug)) {
        errors.push(`miniprogram: visible topic "${slug}" is not render-ready`);
      }
    }
  }
}

if (policy["web-production"]?.visibleTopics !== "all-render-ready") {
  errors.push('web-production: visibleTopics must be "all-render-ready"');
}

if (errors.length > 0) {
  console.error("Compliance validation failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log(
  `Compliance policy checked: ${requiredChannels.length} channels, ${renderReadySlugs.size} render-ready topics`,
);
