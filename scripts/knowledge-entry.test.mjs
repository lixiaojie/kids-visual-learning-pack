import { mkdirSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { join } from "node:path";
import { strict as assert } from "node:assert";
import { execFileSync } from "node:child_process";
import {
  kidsWorldTopicHref,
  legacyTopicPath,
  loadKnowledgeEntry,
  mapIndexedLocation,
  renderHubHtml,
  renderLegacyTopicPageHtml,
  repoRoot,
  resolveTopicSlug,
  RESERVED_PAGE_HASHES,
} from "./knowledge-entry.mjs";

const root = repoRoot();
const read = (relative) => readFileSync(join(root, relative), "utf8");
const entry = loadKnowledgeEntry(root);
const indexHtml = read("index.html");
const homePage = read("boards/kids-world/src/pages/HomePage.tsx");
const notice = read("boards/kids-world/src/components/home/KnowledgeEntryNotice.tsx");
const nginx = read("ops/cognitive-card-server/nginx/card-os.conf");
const route = read("boards/kids-world/src/lib/legacy-topic-route.ts");

assert.equal(entry.schema, "yutou-knowledge-entry-v1");
assert.equal(entry.activeMode, "card-os");
assert.equal(entry.cardOsPublicUrl, "https://www.yutou.space/card-os/");
assert.equal(entry.kidsWorldArchiveHref, "boards/kids-world/index.html");
assert.deepEqual(entry.hiddenInProduction, ["spider-verse", "paw-patrol"]);
assert.equal(entry.modes.parallel.primaryId, "kids-world");
assert.equal(entry.modes.parallel.secondaryId, "card-os");
assert.equal(entry.modes["card-os"].primaryId, "card-os");
assert.equal(entry.modes["card-os"].secondaryId, "kids-world");
assert.equal(entry.frozenKidsWorldTopics.length, 13);
assert.ok(entry.frozenKidsWorldTopics.includes("cicada-life"));
assert.ok(entry.frozenKidsWorldTopics.includes("dinosaurs"));
assert.deepEqual(entry.reservedPageHashes, RESERVED_PAGE_HASHES);
assert.equal(entry.legacyPathPattern, "boards/{slug}/index.html");

assert.equal(renderHubHtml(entry), indexHtml);
assert.equal(false, /http-equiv=["']refresh["']/i.test(indexHtml));
const primary = indexHtml.match(
  /data-knowledge-entry="primary"[^>]*href="([^"]+)"/,
);
const archive = indexHtml.match(
  /data-knowledge-entry="archive"[^>]*href="([^"]+)"/,
);
assert.ok(primary, "root hub must mark the primary knowledge entry");
assert.ok(archive, "root hub must keep the frozen kids-world archive");
assert.equal(primary[1], entry.cardOsPublicUrl);
assert.equal(archive[1], entry.kidsWorldArchiveHref);
assert.equal(false, indexHtml.includes("spider-verse"));
assert.equal(false, indexHtml.includes("paw-patrol"));
assert.ok(indexHtml.includes('name="viewport"'));
assert.ok(indexHtml.includes("旧知识站"));

const parallelHub = renderHubHtml({ ...entry, activeMode: "parallel" });
assert.equal(false, /http-equiv=["']refresh["']/i.test(parallelHub));
const parallelPrimary = parallelHub.match(
  /data-knowledge-entry="primary"[^>]*href="([^"]+)"/,
);
const parallelSecondary = parallelHub.match(
  /data-knowledge-entry="secondary"[^>]*href="([^"]+)"/,
);
assert.ok(parallelPrimary, "parallel hub must mark kids-world as primary");
assert.ok(parallelSecondary, "parallel hub must keep Card OS as secondary");
assert.equal(parallelPrimary[1], entry.kidsWorldArchiveHref);
assert.equal(parallelSecondary[1], entry.cardOsPublicUrl);
assert.equal(false, parallelHub.includes("spider-verse"));
assert.equal(false, parallelHub.includes("paw-patrol"));

assert.ok(homePage.includes("KnowledgeEntryNotice"));
assert.ok(notice.includes("knowledge-entry-notice"));
assert.ok(notice.includes(entry.cardOsPublicUrl) || notice.includes("cardOsPublicUrl"));
assert.ok(route.includes("RESERVED_PAGE_HASHES"));

assert.equal(resolveTopicSlug("", "#worlds"), null);
assert.equal(resolveTopicSlug("", "#recent-observation"), null);
assert.equal(resolveTopicSlug("", "#"), null);
assert.equal(resolveTopicSlug("?topic=dinosaurs", "#worlds"), "dinosaurs");

for (const slug of entry.frozenKidsWorldTopics) {
  assert.equal(resolveTopicSlug("", `#${slug}`), slug);
  assert.equal(resolveTopicSlug("", `#topic/${slug}`), slug);
  assert.equal(resolveTopicSlug(`?topic=${slug}`, ""), slug);

  const hashHit = mapIndexedLocation(
    { pathname: "boards/kids-world/index.html", hash: `#${slug}` },
    entry,
  );
  assert.equal(hashHit.kind, "archive-topic");
  assert.equal(hashHit.slug, slug);
  assert.equal(hashHit.archiveHref, kidsWorldTopicHref(slug));

  const pathHit = mapIndexedLocation({ pathname: legacyTopicPath(slug) }, entry);
  assert.equal(pathHit.kind, "substitute-page");
  assert.equal(pathHit.slug, slug);
  assert.equal(pathHit.archiveHref, kidsWorldTopicHref(slug));
  assert.equal(pathHit.galleryHref, entry.cardOsPublicUrl);

  const page = renderLegacyTopicPageHtml(slug, slug, entry);
  assert.ok(page.includes("旧链接说明"));
  assert.ok(page.includes(`#topic/${slug}`));
  assert.ok(page.includes(entry.cardOsPublicUrl));
  assert.equal(false, /http-equiv=["']refresh["']/i.test(page));
}

const unknownTopic = mapIndexedLocation(
  { pathname: "boards/kids-world/index.html", hash: "#immune-system" },
  entry,
);
assert.equal(unknownTopic.kind, "unknown-topic");
assert.equal(unknownTopic.slug, "immune-system");

assert.equal(false, nginx.includes("return 307 /card-os/api/v1/capabilities"));
assert.ok(nginx.includes("location ^~ /card-os/packages/"));
assert.ok(nginx.includes("proxy_pass http://127.0.0.1:8765;"));

mkdirSync(join(root, "tmp"), { recursive: true });
const staging = mkdtempSync(join(root, "tmp/knowledge-entry-"));
try {
  execFileSync("node", ["scripts/render-knowledge-entry.mjs", "--legacy-out", staging], {
    cwd: root,
    stdio: "pipe",
  });
  for (const slug of entry.frozenKidsWorldTopics) {
    const page = readFileSync(join(staging, slug, "index.html"), "utf8");
    assert.ok(page.includes("打开旧主题页"));
    assert.ok(page.includes(`#topic/${slug}`));
  }
} finally {
  rmSync(staging, { recursive: true, force: true });
}

console.log("Knowledge entry contract checks passed");
