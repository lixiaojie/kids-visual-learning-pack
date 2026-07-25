import assert from "node:assert/strict";
import fs from "node:fs";

const deployScript = fs.readFileSync(new URL("./deploy.sh", import.meta.url), "utf8");

assert.match(
  deployScript,
  /^npm run build:kids-world$/m,
  "deploy.sh must use the canonical kids-world build command so the root Vite config is loaded",
);
assert.match(
  deployScript,
  /^npm run build:paw$/m,
  "deploy.sh must use the canonical paw-patrol build command",
);
assert.doesNotMatch(
  deployScript,
  /^npx vite build boards\/kids-world\b/m,
  "deploy.sh must not duplicate the kids-world Vite command",
);

console.log("deployment build entrypoints checked");
