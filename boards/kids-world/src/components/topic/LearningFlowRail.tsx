import type { LearningFlowStage, Locale } from "@yutou/kids-content";

type Props = {
  activeStageId: string;
  stages: LearningFlowStage[];
  locale: Locale;
};

export function LearningFlowRail({ activeStageId, stages, locale }: Props) {
  function scrollToStage(stage: LearningFlowStage) {
    const section = stage.sectionIds.map((id) => document.getElementById(id)).find(Boolean);
    section?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <nav className="learning-flow-rail" aria-label={locale === "zh-CN" ? "学习流程" : "Learning flow"}>
      {stages.map((stage, index) => (
        <button
          className={activeStageId === stage.id ? "active" : ""}
          key={stage.id}
          type="button"
          onClick={() => scrollToStage(stage)}
        >
          <span>{index + 1}</span>
          <strong>{stage.label}</strong>
          <small>{stage.childPrompt}</small>
        </button>
      ))}
    </nav>
  );
}
