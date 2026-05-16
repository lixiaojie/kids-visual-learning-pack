export type Locale = "zh-CN" | "en-US";
export type EvidenceStatus = "idle" | "selected" | "correct" | "wrong" | "partial" | "complete";
export type TaskResult = EvidenceStatus;
export type TextMap = Record<string, string>;

export type VisualFocusMode =
  | "whole-image"
  | "whole"
  | "hotspot"
  | "group"
  | "path-step"
  | "sequence-progress"
  | "compare-side"
  | "task-option"
  | "zoom"
  | "callout"
  | "none";

export type VisualFocusRegion = {
  id: string;
  label?: string;
  x: number;
  y: number;
  width: number;
  height: number;
  emphasis?: "primary" | "supporting" | "warning";
};

export type VisualFocus = {
  mode: VisualFocusMode;
  regions?: VisualFocusRegion[];
  activeRegionIds?: string[];
  dimOthers?: boolean;
  progress?: {
    current: number;
    total: number;
  };
  zoom?: {
    x: number;
    y: number;
    scale: number;
  };
};

export type VisualSlotRole = "hero" | "observation" | "process" | "compare" | "task" | "summary";

export type VisualSlotTarget =
  | "hero"
  | "classificationGroups"
  | "representativeObjects"
  | "mechanism"
  | "secondaryMechanism"
  | "comparePairs"
  | "clickTasks"
  | "parentTips"
  | `classificationGroups.${string}`
  | `representativeObjects.${string}`
  | `mechanism.${string}`
  | `secondaryMechanism.${string}`
  | `comparePairs.${string}`
  | `clickTasks.${string}`;

export type EvidenceSourcePath =
  | `classificationGroups.${string}`
  | `representativeObjects.${string}`
  | `mechanism.steps.${string}`
  | `secondaryMechanism.steps.${string}`
  | `comparePairs.${string}`
  | `comparePairs.${string}#a`
  | `comparePairs.${string}#b`
  | `clickTasks.${string}`
  | `clickTasks.${string}.options.${string}`;

export type VisualSlot = {
  id: string;
  assetId: string;
  target: VisualSlotTarget;
  role: VisualSlotRole;
  required?: boolean;
  caption?: string;
  alt?: string;
};

export type LearningFlowStage = {
  id: string;
  label: string;
  sectionIds: string[];
  visualSlotId?: string;
  childPrompt: string;
  defaultEvidenceSource?: EvidenceSourcePath;
};

export type EvidenceMarkerChip = {
  label: string;
  meaning: string;
  emphasis?: "primary" | "supporting" | "warning";
};

export type VisualEvidenceBinding = {
  id: string;
  source: EvidenceSourcePath;
  visualSlotId: string;
  interactionScope?: "local" | "linkedObjects" | "linkedEvidence" | "flowNavigation";
  evidenceTitle: string;
  observePrompt?: string;
  evidenceCopy: string;
  markerChips?: EvidenceMarkerChip[];
  expectedStatus?: Exclude<EvidenceStatus, "idle">;
  nextPrompt?: string;
  quality?: "curated" | "generated" | "derived-fallback";
  focus?: VisualFocus;
};

export type VisualEvidenceState = {
  source: EvidenceSourcePath;
  sourceId: string;
  visualSlotId: string;
  status: EvidenceStatus;
  evidenceTitle: string;
  observePrompt?: string;
  evidenceCopy: string;
  selectedLabels?: string[];
  markerChips?: EvidenceMarkerChip[];
  explanationLevel?: "child" | "parent";
  bindingQuality: "explicit" | "derived";
  nextPrompt?: string;
  focus?: VisualFocus;
};

export type EvidenceResolveContext = {
  source: EvidenceSourcePath;
  selectedIds?: string[];
  result?: EvidenceStatus;
  locale?: Locale;
};

export type EvidenceCoverageReport = {
  slug: string;
  totalInteractiveSources: number;
  resolvedEvidenceSources: number;
  unresolvedSources: string[];
  explicitBindingCount: number;
  derivedBindingCount: number;
  clickTaskOptionCoverage: number;
  mechanismStepCoverage: number;
  comparePairCoverage: number;
  representativeObjectCoverage: number;
  derivedFallbackRatio: number;
  pass: boolean;
};

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
  observationContext?: {
    source: string;
    scene: string;
    trigger: string;
    season?: string;
    safetyNote?: string;
  };
  cognitiveFocus?: string[];
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
  visualSlots?: VisualSlot[];
  learningFlow?: LearningFlowStage[];
  visualEvidenceBindings?: VisualEvidenceBinding[];
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
