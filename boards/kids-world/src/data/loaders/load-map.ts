import type { ExplorationMap } from "../../types/world";
import type { Locale } from "../../types/topic";
import explorationMapBase from "../exploration-map.json";
import explorationMapEn from "../locales/en-US/exploration-map.json";
import { deepMerge } from "./locale-merge";

export function getMap(locale: Locale): ExplorationMap {
  const base = explorationMapBase as unknown as ExplorationMap;
  return locale === "en-US" ? deepMerge(base, explorationMapEn) : base;
}
