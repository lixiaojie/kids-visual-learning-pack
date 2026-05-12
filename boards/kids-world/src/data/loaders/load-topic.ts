import type { Locale, Topic } from "../../types/topic";
import { deepMerge } from "./locale-merge";

import animalTreeBase from "../topics/animal-classification-tree.json";
import animalTreeEn from "../locales/en-US/topics/animal-classification-tree.json";
import bloodCellsBase from "../topics/blood-cells-3d.json";
import bloodCellsEn from "../locales/en-US/topics/blood-cells-3d.json";
import climateBase from "../topics/earth-climate-cities.json";
import climateEn from "../locales/en-US/topics/earth-climate-cities.json";
import digestionBase from "../topics/digestion.json";
import digestionEn from "../locales/en-US/topics/digestion.json";
import dinosaursBase from "../topics/dinosaurs.json";
import dinosaursEn from "../locales/en-US/topics/dinosaurs.json";
import ecosystemBase from "../topics/ecosystem.json";
import ecosystemEn from "../locales/en-US/topics/ecosystem.json";
import insectsBase from "../topics/insects-and-spiders.json";
import insectsEn from "../locales/en-US/topics/insects-and-spiders.json";
import llmBase from "../topics/llm-kids-basics.json";
import llmEn from "../locales/en-US/topics/llm-kids-basics.json";
import moonPhasesBase from "../topics/moon-phases.json";
import moonPhasesEn from "../locales/en-US/topics/moon-phases.json";
import robotsBase from "../topics/robots.json";
import robotsEn from "../locales/en-US/topics/robots.json";
import solarBase from "../topics/solar-system-overview.json";
import solarEn from "../locales/en-US/topics/solar-system-overview.json";
import waterCycleBase from "../topics/water-cycle.json";
import waterCycleEn from "../locales/en-US/topics/water-cycle.json";

const topicBaseBySlug = {
  "animal-classification-tree": animalTreeBase as unknown as Topic,
  "blood-cells-3d": bloodCellsBase as unknown as Topic,
  digestion: digestionBase as unknown as Topic,
  dinosaurs: dinosaursBase as unknown as Topic,
  "earth-climate-cities": climateBase as unknown as Topic,
  ecosystem: ecosystemBase as unknown as Topic,
  "insects-and-spiders": insectsBase as unknown as Topic,
  "llm-kids-basics": llmBase as unknown as Topic,
  "moon-phases": moonPhasesBase as unknown as Topic,
  robots: robotsBase as unknown as Topic,
  "solar-system-overview": solarBase as unknown as Topic,
  "water-cycle": waterCycleBase as unknown as Topic,
};

const topicEnBySlug = {
  "animal-classification-tree": animalTreeEn as unknown as Partial<Topic>,
  "blood-cells-3d": bloodCellsEn as unknown as Partial<Topic>,
  digestion: digestionEn as unknown as Partial<Topic>,
  dinosaurs: dinosaursEn as unknown as Partial<Topic>,
  "earth-climate-cities": climateEn as unknown as Partial<Topic>,
  ecosystem: ecosystemEn as unknown as Partial<Topic>,
  "insects-and-spiders": insectsEn as unknown as Partial<Topic>,
  "llm-kids-basics": llmEn as unknown as Partial<Topic>,
  "moon-phases": moonPhasesEn as unknown as Partial<Topic>,
  robots: robotsEn as unknown as Partial<Topic>,
  "solar-system-overview": solarEn as unknown as Partial<Topic>,
  "water-cycle": waterCycleEn as unknown as Partial<Topic>,
};

export function getTopic(slug: string, locale: Locale): Topic | null {
  const base = topicBaseBySlug[slug as keyof typeof topicBaseBySlug];
  if (!base) return null;
  return locale === "en-US" ? deepMerge(base, topicEnBySlug[slug as keyof typeof topicEnBySlug]) : base;
}

export function hasTopicData(slug: string): boolean {
  return slug in topicBaseBySlug;
}
