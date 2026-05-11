import Ajv from "ajv/dist/2020.js";
import { readFileSync, readdirSync } from "node:fs";
import { join, basename } from "node:path";

const TOPICS_DIR = "boards/kids-world/src/data/topics";
const SCHEMA_PATH = "boards/kids-world/src/data/schema/topic.schema.json";
const REGISTRY_PATH = "boards/kids-world/src/data/topic-registry.json";

const schema = JSON.parse(readFileSync(SCHEMA_PATH, "utf-8"));
const registry = JSON.parse(readFileSync(REGISTRY_PATH, "utf-8"));
const registrySlugs = new Set(registry.topics.map((t) => t.slug));

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
