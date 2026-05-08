import { readFileSync } from "node:fs";
import { strict as assert } from "node:assert";

const html = readFileSync(new URL("./index.html", import.meta.url), "utf8");

const mainCards = [...html.matchAll(/<section[^>]+class="[^"]*\bcard\b[^"]*"[^>]+id="card-\d+"/g)];
const appendices = [...html.matchAll(/<section[^>]+class="[^"]*\bappendix-card\b[^"]*"[^>]+id="appendix-[ab]"/g)];
const navLinks = [...html.matchAll(/<a href="#(?:card-\d+|appendix-[ab])">/g)];
const detailButtons = [...html.matchAll(/data-detail/g)];

assert.equal(mainCards.length, 10, "Spider-Verse board should expose 10 main story cards");
assert.equal(appendices.length, 2, "Spider-Verse board should expose 2 parent appendix sections");
assert.equal(navLinks.length, 12, "Top navigation should link to all cards and appendices");
assert.ok(html.includes("data-print"), "Print button must be preserved");
assert.ok(detailButtons.length >= 12, "Cards should include clickable child/parent detail affordances");
assert.ok(html.includes("角色大合影"), "Card 01 should focus on recognizing characters");
assert.ok(html.includes("Miles 身边的人"), "Card 02 should focus on relationships");
assert.ok(html.includes("第一部剧情地图"), "Card 04 should include the first movie storyboard");
assert.ok(html.includes("第二部剧情地图"), "Card 05 should include the second movie storyboard");
assert.ok(html.includes("我的蜘蛛英雄创作卡"), "Card 10 should provide an original hero creation sheet");

console.log("Spider-Verse structure checks passed");
