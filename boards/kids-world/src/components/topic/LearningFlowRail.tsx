import type { LearningFlowStage, Locale } from "@yutou/kids-content";

type Props = {
  activeStageId: string;
  stages: LearningFlowStage[];
  locale: Locale;
  onSelectStage: (stageId: string) => void;
  collapsed?: boolean;
  hidden?: boolean;
  onExpand?: () => void;
};

export function LearningFlowRail({ activeStageId, stages, locale, onSelectStage, collapsed = false, hidden = false, onExpand }: Props) {
  function scrollToStage(stage: LearningFlowStage) {
    const section = stage.sectionIds.map((id) => document.getElementById(id)).find(Boolean);
    section?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const activeStageIndex = Math.max(0, stages.findIndex((stage) => stage.id === activeStageId));
  const activeStage = stages[activeStageIndex] ?? stages[0];

  return (
    <nav className={`learning-flow-rail ${collapsed ? "is-collapsed" : ""} ${hidden ? "is-hidden" : ""}`} aria-label={locale === "zh-CN" ? "学习流程" : "Learning flow"}>
      {collapsed && activeStage ? (
        <button className="learning-flow-status" type="button" onClick={() => onExpand?.()} aria-label={locale === "zh-CN" ? "展开学习流程" : "Expand learning flow"}>
          {activeStageIndex + 1}. {activeStage.label}
        </button>
      ) : null}
      {stages.map((stage, index) => (
        <button
          className={activeStageId === stage.id ? "active" : ""}
          key={stage.id}
          type="button"
          onClick={() => {
            onSelectStage(stage.id);
            scrollToStage(stage);
          }}
        >
          <span>{index + 1}</span>
          <strong>{stage.label}</strong>
          <small>{stage.childPrompt}</small>
        </button>
      ))}
    </nav>
  );
}
