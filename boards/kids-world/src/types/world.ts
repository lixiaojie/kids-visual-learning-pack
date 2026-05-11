export type TopicCard = {
  id?: string;
  slug?: string;
  title: string;
  status: string;
  cardDescription: string;
  childDescription?: string;
  learningGoalTags?: string[];
  suggestedRoute?: string;
  href?: string;
};

export type World = {
  id: string;
  type: string;
  name: string;
  status: string;
  recommendedColor: { hex: string; softHex: string };
  childOneLiner: string;
  parentNote: string;
  entryCard: { title: string; subtitle: string; cta: string; badge: string };
  topicCards: TopicCard[];
};

export type ExplorationMap = {
  title: string;
  subtitle: string;
  homeHero: {
    title: string;
    subtitle: string;
    childIntro: string;
    parentIntro: string;
    primaryCTA: string;
    secondaryCTA: string;
  };
  sections: Array<{ id: string; title: string; description: string; worlds: string[] }>;
  statusLegend: Array<{ status: string; label: string; childLabel: string; description: string }>;
  worlds: World[];
};
