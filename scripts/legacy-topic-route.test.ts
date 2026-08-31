import { strict as assert } from "node:assert";
import { resolveTopicSlug } from "../boards/kids-world/src/lib/legacy-topic-route";

assert.equal(resolveTopicSlug("", "#dinosaurs"), "dinosaurs");
assert.equal(resolveTopicSlug("", "#topic/dinosaurs"), "dinosaurs");
assert.equal(resolveTopicSlug("?topic=cicada-life", ""), "cicada-life");
assert.equal(resolveTopicSlug("", "#worlds"), null);
assert.equal(resolveTopicSlug("", "#recent-observation"), null);
assert.equal(resolveTopicSlug("", "#"), null);
assert.equal(resolveTopicSlug("", "#topic/insects-and-spiders"), "insects-and-spiders");
assert.equal(resolveTopicSlug("", "#not/a-slug"), null);

console.log("Legacy topic route checks passed");
