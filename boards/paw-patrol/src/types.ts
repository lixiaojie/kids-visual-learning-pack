export type TabKey = "home" | "characters" | "map" | "gear" | "mission" | "flow" | "story" | "badges";

export type Character = {
  id: string;
  nameZh: string;
  nameEn: string;
  role: string;
  shortRole: string;
  vehicle: string;
  tools: string[];
  strengths: string[];
  bestFor: string[];
  badgeId: string;
  colorHint: string;
  childIntro: string;
  parentNote: string;
};

export type Mission = {
  id: string;
  title: string;
  locationId: string;
  problemType: string;
  description: string;
  recommendedCharacterIds: string[];
  bestCharacterId: string;
  helperCharacterIds?: string[];
  reason: string;
  wrongChoiceHint: string;
  badgeRewardId: string;
};

export type Badge = {
  id: string;
  name: string;
  meaning: string;
  childText: string;
  relatedCharacterIds: string[];
  icon: string;
};

export type Location = {
  id: string;
  name: string;
  description: string;
  commonProblems: string[];
  recommendedCharacterIds: string[];
  icon: string;
};

export type GearItem = {
  id: string;
  name: string;
  characterId: string;
  type: "vehicle" | "tool";
  functions: string[];
  bestForProblemTypes: string[];
};
