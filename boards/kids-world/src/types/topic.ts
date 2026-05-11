export type Locale = "zh-CN" | "en-US";
export type TaskResult = "idle" | "correct" | "wrong";
export type TextMap = Record<string, string>;

export type ClickTask = {
  id: string;
  type: "singleChoice" | "findTarget" | "sequenceClick" | string;
  title: string;
  prompt?: string;
  options?: Array<{ id: string; label: string }>;
  correctOptionId?: string;
  correctSequence?: string[];
  targetIds?: string[];
  decoyIds?: string[];
  wrongHint?: string;
  wrongHints?: TextMap;
  successCopy?: string;
};

export type Topic = {
  slug: string;
  title: string;
  subtitle: string;
  pageType: string;
  coreQuestion: string;
  learningGoals: string[];
  relatedTopics: string[];
  hero: {
    title: string;
    kicker: string;
    lead: string;
    sceneExplanation: string;
    childPrompt: string;
    parentPrompt: string;
    placeholder?: { type?: string; asset?: string };
  };
  assets?: Record<string, { path: string; purpose?: string; status?: string }>;
  classificationGroups: Array<{
    id: string;
    name: string;
    childExplanation: string;
    parentNote?: string;
  }>;
  representativeObjects: Array<{
    id: string;
    name: string;
    groupId: string;
    childExplanation: string;
    visualHint: string;
    commonMisread?: string;
  }>;
  mechanism: {
    title?: string;
    steps: Array<{ id: string; shortTitle: string; childExplanation: string; parentNote?: string }>;
  };
  secondaryMechanism?: {
    title: string;
    steps: Array<{ id: string; shortTitle: string; childExplanation: string; parentNote?: string }>;
  };
  comparePairs: Array<{
    id: string;
    title: string;
    a: { name: string; points: string[] };
    b: { name: string; points: string[] };
    childConclusion: string;
  }>;
  clickTasks: ClickTask[];
  speakTemplates: string[];
  parentTips: string[];
};
