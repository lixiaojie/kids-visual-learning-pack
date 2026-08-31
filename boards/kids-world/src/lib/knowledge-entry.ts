import entry from "../../../../shared/knowledge-entry.json";

export const knowledgeEntry = entry;

export function isCardOsKnowledgeHome() {
  return entry.activeMode === "card-os";
}
