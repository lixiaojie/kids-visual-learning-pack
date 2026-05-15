import Ajv from "ajv/dist/2020.js";
import { readFileSync, readdirSync } from "node:fs";
import { join, basename } from "node:path";

const TOPICS_DIR = "boards/kids-world/src/data/topics";
const SCHEMA_PATH = "boards/kids-world/src/data/schema/topic.schema.json";
const REGISTRY_PATH = "boards/kids-world/src/data/topic-registry.json";

const schema = JSON.parse(readFileSync(SCHEMA_PATH, "utf-8"));
const registry = JSON.parse(readFileSync(REGISTRY_PATH, "utf-8"));
const manifest = JSON.parse(readFileSync("boards/kids-world/src/data/image-generation-manifest.json", "utf-8"));
const registrySlugs = new Set(registry.topics.map((t) => t.slug));
const manifestAssetIds = new Set((manifest.assets || []).map((asset) => asset.assetId));

const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(schema);

const files = readdirSync(TOPICS_DIR).filter((f) => f.endsWith(".json"));
let totalErrors = 0;

for (const file of files) {
  const path = join(TOPICS_DIR, file);
  const topic = JSON.parse(readFileSync(path, "utf-8"));
  const errors = [];

  // Schema validation
  if (!validate(topic)) {
    for (const err of validate.errors) {
      errors.push(`schema: ${err.instancePath} ${err.message}`);
    }
  }

  // Slug matches filename
  const expectedSlug = basename(file, ".json");
  if (topic.slug !== expectedSlug) {
    errors.push(`slug "${topic.slug}" does not match filename "${expectedSlug}"`);
  }

  // classificationGroups IDs unique
  if (topic.classificationGroups) {
    const groupIds = topic.classificationGroups.map((g) => g.id);
    const dupes = groupIds.filter((id, i) => groupIds.indexOf(id) !== i);
    if (dupes.length > 0) {
      errors.push(`duplicate classificationGroup IDs: ${dupes.join(", ")}`);
    }

    // representativeObjects.groupId references valid group
    if (topic.representativeObjects) {
      const groupIdSet = new Set(groupIds);
      for (const obj of topic.representativeObjects) {
        if (obj.groupId && !groupIdSet.has(obj.groupId)) {
          errors.push(`object "${obj.id}" has groupId "${obj.groupId}" not in classificationGroups`);
        }
      }
    }
  }

  // clickTasks referential integrity
  if (topic.clickTasks) {
    for (const task of topic.clickTasks) {
      const optionIds = new Set((task.options || []).map((o) => o.id));

      if (task.type === "singleChoice") {
        if (task.correctOptionId && !optionIds.has(task.correctOptionId)) {
          errors.push(`clickTask "${task.id}": correctOptionId "${task.correctOptionId}" not in options`);
        }
      }

      if (task.type === "findTarget") {
        const allIds = new Set([...(task.targetIds || []), ...(task.decoyIds || [])]);
        for (const id of task.targetIds || []) {
          if (!allIds.has(id)) {
            errors.push(`clickTask "${task.id}": targetId "${id}" not in combined options`);
          }
        }
      }

      if (task.type === "sequenceClick") {
        for (const id of task.correctSequence || []) {
          if (!optionIds.has(id)) {
            errors.push(`clickTask "${task.id}": correctSequence id "${id}" not in options`);
          }
        }
      }
    }
  }

  // visualSlots referential integrity
  const visualSlotIds = new Set();
  if (topic.visualSlots) {
    const slotIds = topic.visualSlots.map((slot) => slot.id);
    slotIds.forEach((id) => visualSlotIds.add(id));
    const duplicateSlotIds = slotIds.filter((id, i) => slotIds.indexOf(id) !== i);
    if (duplicateSlotIds.length > 0) {
      errors.push(`duplicate visualSlot IDs: ${duplicateSlotIds.join(", ")}`);
    }

    for (const slot of topic.visualSlots) {
      if (!manifestAssetIds.has(slot.assetId)) {
        errors.push(`visualSlot "${slot.id}": assetId "${slot.assetId}" not in image-generation-manifest`);
      }

      const [moduleName, itemId] = String(slot.target).split(".");
      if (itemId) {
        if (moduleName === "classificationGroups" && !topic.classificationGroups?.some((item) => item.id === itemId)) {
          errors.push(`visualSlot "${slot.id}": target "${slot.target}" does not match a classificationGroup`);
        }
        if (moduleName === "representativeObjects" && !topic.representativeObjects?.some((item) => item.id === itemId)) {
          errors.push(`visualSlot "${slot.id}": target "${slot.target}" does not match a representativeObject`);
        }
        if (moduleName === "mechanism" && !topic.mechanism?.steps?.some((item) => item.id === itemId)) {
          errors.push(`visualSlot "${slot.id}": target "${slot.target}" does not match a mechanism step`);
        }
        if (moduleName === "secondaryMechanism" && !topic.secondaryMechanism?.steps?.some((item) => item.id === itemId)) {
          errors.push(`visualSlot "${slot.id}": target "${slot.target}" does not match a secondaryMechanism step`);
        }
        if (moduleName === "comparePairs" && !topic.comparePairs?.some((item) => item.id === itemId)) {
          errors.push(`visualSlot "${slot.id}": target "${slot.target}" does not match a comparePair`);
        }
        if (moduleName === "clickTasks" && !topic.clickTasks?.some((item) => item.id === itemId)) {
          errors.push(`visualSlot "${slot.id}": target "${slot.target}" does not match a clickTask`);
        }
      }
    }
  }

  // visualEvidenceBindings referential integrity
  if (topic.visualEvidenceBindings) {
    const bindingIds = topic.visualEvidenceBindings.map((binding) => binding.id);
    const duplicateBindingIds = bindingIds.filter((id, i) => bindingIds.indexOf(id) !== i);
    if (duplicateBindingIds.length > 0) {
      errors.push(`duplicate visualEvidenceBinding IDs: ${duplicateBindingIds.join(", ")}`);
    }

    for (const binding of topic.visualEvidenceBindings) {
      if (!visualSlotIds.has(binding.visualSlotId)) {
        errors.push(`visualEvidenceBinding "${binding.id}": visualSlotId "${binding.visualSlotId}" does not exist`);
      }

      const source = String(binding.source);
      const parts = source.split(".");
      if (parts[0] === "classificationGroups" && !topic.classificationGroups?.some((item) => item.id === parts[1])) {
        errors.push(`visualEvidenceBinding "${binding.id}": source "${source}" does not match a classificationGroup`);
      }
      if (parts[0] === "representativeObjects" && !topic.representativeObjects?.some((item) => item.id === parts[1])) {
        errors.push(`visualEvidenceBinding "${binding.id}": source "${source}" does not match a representativeObject`);
      }
      if (parts[0] === "mechanism" && parts[1] === "steps" && !topic.mechanism?.steps?.some((item) => item.id === parts[2])) {
        errors.push(`visualEvidenceBinding "${binding.id}": source "${source}" does not match a mechanism step`);
      }
      if (parts[0] === "secondaryMechanism" && parts[1] === "steps" && !topic.secondaryMechanism?.steps?.some((item) => item.id === parts[2])) {
        errors.push(`visualEvidenceBinding "${binding.id}": source "${source}" does not match a secondaryMechanism step`);
      }
      if (parts[0] === "comparePairs" && !topic.comparePairs?.some((item) => item.id === parts[1])) {
        errors.push(`visualEvidenceBinding "${binding.id}": source "${source}" does not match a comparePair`);
      }
      if (parts[0] === "clickTasks") {
        const task = topic.clickTasks?.find((item) => item.id === parts[1]);
        if (!task) {
          errors.push(`visualEvidenceBinding "${binding.id}": source "${source}" does not match a clickTask`);
        }
        if (task && parts[2] === "options") {
          const optionIds = new Set(
            (task.options || [...(task.targetIds || []), ...(task.decoyIds || [])].map((id) => ({ id }))).map((option) => option.id),
          );
          if (!optionIds.has(parts[3])) {
            errors.push(`visualEvidenceBinding "${binding.id}": source "${source}" does not match a clickTask option`);
          }
        }
      }
    }
  }

  // relatedTopics reference valid slugs
  if (topic.relatedTopics) {
    for (const slug of topic.relatedTopics) {
      if (!registrySlugs.has(slug)) {
        errors.push(`relatedTopics: slug "${slug}" not in topic-registry`);
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

console.log(`\n${files.length} files checked, ${totalErrors} errors`);
if (totalErrors > 0) process.exit(1);
