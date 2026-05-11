import { existsSync, readFileSync } from "node:fs";
import { strict as assert } from "node:assert";

const html = readFileSync(new URL("./index.html", import.meta.url), "utf8");
const script = readFileSync(new URL("./script.js", import.meta.url), "utf8");

const sections = [...html.matchAll(/<section[^>]+class="[^"]*\bboard-section\b[^"]*"[^>]+id="section-\d+"/g)];
const navLinks = [...html.matchAll(/<a href="#(?:hero|section-\d+|appendix)">/g)];
const configuredImages = [...script.matchAll(/assets\/(?:cast|characters|relationships|story-01|story-02|boards)\/[^"'`]+?\.(?:png|jpg|jpeg|webp)/g)];
const webpImages = [...new Set([...html, script].join("\n").match(/assets\/(?:cast|characters|relationships|story-01|story-02|boards)\/[^"'`]+?\.webp/g) ?? [])];

assert.ok(html.includes('data-mode="child"'), "Page should default to child mode");
assert.ok(html.includes('data-mode-toggle'), "Header should include child/parent mode toggle");
assert.ok(html.includes('id="hero"'), "Page should include a hero overview section");
assert.equal(sections.length, 10, "Spider board should expose 10 main visual sections");
assert.ok(html.includes('id="appendix"'), "Page should include a parent appendix section");
assert.equal(navLinks.length, 12, "Top navigation should link to hero, sections, and appendix");
assert.ok(html.includes('href="../../index.html"'), "Header should include a link back to the home page");
assert.ok(html.includes("data-reset"), "Header should include a reset control for page state");
assert.ok(html.includes("data-print"), "Print button must be preserved");
assert.ok(html.includes('id="story-modal"'), "Story cards should have a modal for enlarged explanation");
assert.ok(script.includes("document.body.dataset.mode"), "Mode toggle should update body dataset mode");
assert.ok(script.includes("wireReset"), "Reset control should restore interactive page state");
assert.ok(script.includes("renderStoryGrid"), "Story grids should be rendered from data");
assert.ok(script.includes("openStoryModal"), "Story cards should open enlarged explanation");
assert.ok(configuredImages.length >= 45, "Script should configure the generated image asset paths");
assert.ok(script.includes("assets/cast/cast-lineup.webp"), "Hero should use the deployment WebP asset path");
assert.ok(script.includes("assets/story-01/01-new-school.webp"), "Story one should use deployment WebP story asset paths");
assert.ok(script.includes("assets/story-02/12-team-up.webp"), "Story two should use deployment WebP story asset paths");
assert.ok(webpImages.length >= 45, "Page should deploy WebP image references");

for (const image of webpImages) {
  const pngSource = image.replace(/\.webp$/, ".png");
  assert.ok(existsSync(new URL(`./${pngSource}`, import.meta.url)), `${pngSource} should exist as the source PNG pair`);
}

console.log("Spider web board structure checks passed");
