import Ajv from "ajv/dist/2020.js";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join, basename } from "node:path";

const OVERLAYS_DIR = "boards/kids-world/src/data/locales/en-US/topics";
const BASE_DIR = "boards/kids-world/src/data/topics";
const SCHEMA_PATH = "boards/kids-world/src/data/schema/i18n-overlay.schema.json";

const schema = JSON.parse(readFileSync(SCHEMA_PATH, "utf-8"));
const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(schema);

// Fields that overlay must NOT modify (structural/logic fields)
const LOCKED_TASK_FIELDS = ["type", "correctOptionId", "correctSequence", "targetIds", "decoyIds"];
const LOCKED_EVIDENCE_FIELDS = ["source", "visualSlotId", "expectedStatus"];

function collectStrings(value, prefix = "") {
  if (typeof value === "string") return [{ path: prefix, value }];
  if (Array.isArray(value)) return value.flatMap((item, index) => collectStrings(item, `${prefix}[${index}]`));
  if (value && typeof value === "object") {
    return Object.entries(value).flatMap(([key, child]) => collectStrings(child, prefix ? `${prefix}.${key}` : key));
  }
  return [];
}

const files = readdirSync(OVERLAYS_DIR).filter((f) => f.endsWith(".json"));
let totalErrors = 0;

for (const file of files) {
  const overlayPath = join(OVERLAYS_DIR, file);
  const basePath = join(BASE_DIR, file);
  const overlay = JSON.parse(readFileSync(overlayPath, "utf-8"));
  const errors = [];

  for (const item of collectStrings(overlay)) {
    if (/[\u3400-\u9fff]/.test(item.value)) {
      errors.push(`${item.path}: en-US overlay contains CJK text`);
    }
  }

  // Schema validation
  if (!validate(overlay)) {
    for (const err of validate.errors) {
      errors.push(`schema: ${err.instancePath} ${err.message}`);
    }
  }

  // Base file must exist
  if (!existsSync(basePath)) {
    errors.push(`no matching base file at ${basePath}`);
  } else {
    const base = JSON.parse(readFileSync(basePath, "utf-8"));

    // id and slug must match base (if present in overlay)
    if (overlay.id !== undefined && overlay.id !== base.id) {
      errors.push(`overlay id "${overlay.id}" differs from base "${base.id}"`);
    }
    if (overlay.slug !== undefined && overlay.slug !== base.slug) {
      errors.push(`overlay slug "${overlay.slug}" differs from base "${base.slug}"`);
    }

    // Check array items have matching IDs
    for (const arrayKey of ["classificationGroups", "representativeObjects", "comparePairs", "clickTasks"]) {
      if (!overlay[arrayKey] || !base[arrayKey]) continue;
      for (let i = 0; i < overlay[arrayKey].length; i++) {
        const overlayItem = overlay[arrayKey][i];
        const baseItem = base[arrayKey][i];
        if (overlayItem?.id && baseItem?.id && overlayItem.id !== baseItem.id) {
          errors.push(`${arrayKey}[${i}].id: overlay "${overlayItem.id}" != base "${baseItem.id}"`);
        }
      }
    }

    // clickTasks must not contain locked fields
    if (overlay.clickTasks) {
      for (const task of overlay.clickTasks) {
        for (const field of LOCKED_TASK_FIELDS) {
          if (field in task) {
            errors.push(`clickTasks "${task.id || "?"}": locked field "${field}" must not appear in overlay`);
          }
        }
      }
    }

    // mechanism steps IDs must match
    for (const mechKey of ["mechanism", "secondaryMechanism"]) {
      if (!overlay[mechKey]?.steps || !base[mechKey]?.steps) continue;
      for (let i = 0; i < overlay[mechKey].steps.length; i++) {
        const oStep = overlay[mechKey].steps[i];
        const bStep = base[mechKey].steps[i];
        if (oStep?.id && bStep?.id && oStep.id !== bStep.id) {
          errors.push(`${mechKey}.steps[${i}].id: overlay "${oStep.id}" != base "${bStep.id}"`);
        }
      }
    }

    if (overlay.visualEvidenceBindings) {
      const baseBindings = new Map((base.visualEvidenceBindings || []).map((binding) => [binding.id, binding]));
      for (const binding of overlay.visualEvidenceBindings) {
        const baseBinding = baseBindings.get(binding.id);
        if (!baseBinding) {
          errors.push(`visualEvidenceBindings "${binding.id || "?"}": no matching base binding`);
          continue;
        }
        for (const field of LOCKED_EVIDENCE_FIELDS) {
          if (field in binding && binding[field] !== baseBinding[field]) {
            errors.push(`visualEvidenceBindings "${binding.id}": locked field "${field}" must match base`);
          }
        }
      }
    }
  }

  if (errors.length > 0) {
    console.log(`❌ ${file}`);
    for (const err of errors) {
      console.log(`   ${err}`);
    }
    totalErrors += errors.length;
  } else {
    console.log(`✅ ${file}`);
  }
}

console.log(`\n${files.length} overlays checked, ${totalErrors} errors`);
if (totalErrors > 0) process.exit(1);
