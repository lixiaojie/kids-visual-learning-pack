import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const root = process.cwd();
const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "interaction-graph-validation-"));

function copyFixturePath(relativePath) {
  const source = path.join(root, relativePath);
  const destination = path.join(fixtureRoot, relativePath);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.cpSync(source, destination, { recursive: true });
}

function runValidator() {
  return spawnSync(process.execPath, ["scripts/validate-interaction-graph.mjs"], {
    cwd: fixtureRoot,
    encoding: "utf8",
  });
}

try {
  copyFixturePath("scripts/validate-interaction-graph.mjs");
  copyFixturePath("packages/kids-content/src");
  copyFixturePath("boards/kids-world/src/data");

  const validResult = runValidator();
  assert.equal(
    validResult.status,
    0,
    `focus-backed representative object bindings should pass:\n${validResult.stderr}${validResult.stdout}`,
  );
  if (validResult.stdout) process.stdout.write(validResult.stdout);
  if (validResult.stderr) process.stderr.write(validResult.stderr);

  const cicadaPath = path.join(fixtureRoot, "boards/kids-world/src/data/topics/cicada-life.json");
  const cicada = JSON.parse(fs.readFileSync(cicadaPath, "utf8"));
  const eggsBinding = cicada.visualEvidenceBindings.find(
    (binding) => binding.source === "representativeObjects.cicadaEggs",
  );
  assert.ok(eggsBinding, "cicadaEggs binding should exist in the controlled fixture");
  eggsBinding.focus.activeRegionIds = eggsBinding.focus.activeRegionIds.filter((id) => id !== "cicadaEggs");
  fs.writeFileSync(cicadaPath, `${JSON.stringify(cicada, null, 2)}\n`);

  const invalidResult = runValidator();
  assert.equal(invalidResult.status, 1, "an exact slot without its object's active focus must fail");
  assert.match(
    invalidResult.stderr,
    /cicada-life representative object cicadaEggs must use a representativeObjects visual slot or focus its own region/,
  );

  eggsBinding.focus.activeRegionIds.push("cicadaEggs");
  eggsBinding.visualSlotId = "missing-slot";
  fs.writeFileSync(cicadaPath, `${JSON.stringify(cicada, null, 2)}\n`);

  const missingSlotResult = runValidator();
  assert.equal(missingSlotResult.status, 1, "an exact focus must still reference an existing visual slot");
  assert.match(
    missingSlotResult.stderr,
    /cicada-life representative object cicadaEggs must use a representativeObjects visual slot or focus its own region/,
  );

  console.log("interaction graph validation regression checks passed");
} finally {
  fs.rmSync(fixtureRoot, { recursive: true, force: true });
}
