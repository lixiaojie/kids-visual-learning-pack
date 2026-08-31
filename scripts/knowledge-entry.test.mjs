import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { strict as assert } from "node:assert";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const read = (relative) => readFileSync(join(root, relative), "utf8");
const entry = JSON.parse(read("shared/knowledge-entry.json"));
const indexHtml = read("index.html");
const homePage = read("boards/kids-world/src/pages/HomePage.tsx");
const nginx = read("ops/cognitive-card-server/nginx/card-os.conf");

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

assert.ok(homePage.includes(entry.cardOsPublicUrl));
assert.ok(homePage.includes("knowledge-entry-notice"));

assert.equal(false, nginx.includes("return 307 /card-os/api/v1/capabilities"));
assert.ok(nginx.includes("location ^~ /card-os/packages/"));
assert.ok(nginx.includes("proxy_pass http://127.0.0.1:8765;"));

console.log("Knowledge entry contract checks passed");
