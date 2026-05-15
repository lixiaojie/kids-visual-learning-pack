import type { Locale, Topic, TopicInteractionAction, TopicInteractionState, TopicPresentation } from "@yutou/kids-content";
import { SectionHeader } from "../shared/SectionHeader";
import { ClickTaskCard } from "./ClickTaskCard";
import { TopicVisual } from "./TopicVisual";

type Props = {
  topic: Topic;
  state: TopicInteractionState;
  presentation: TopicPresentation;
  dispatch: (action: TopicInteractionAction) => void;
  locale: Locale;
};

export function ClickTaskDeck({ topic, state, presentation, dispatch, locale }: Props) {
  const activeTaskId = state.activeTaskId ?? topic.clickTasks[0]?.id ?? "";
  const taskEvidence = presentation.evidence?.source.startsWith("clickTasks.") ? presentation.evidence : null;
  const taskVisualSlot = taskEvidence
    ? presentation.visualSlot
    : topic.visualSlots?.find((slot) => slot.target === `clickTasks.${activeTaskId}`) ??
      topic.visualSlots?.find((slot) => slot.target === "clickTasks");

  return (
    <article className="panel wide" id="topic-tasks">
      <SectionHeader title={locale === "zh-CN" ? "点击任务" : "Tap tasks"} kicker={locale === "zh-CN" ? "不计分，多试几次" : "No score pressure"} />
      <TopicVisual slot={taskVisualSlot} evidence={taskEvidence} fallbackAlt={locale === "zh-CN" ? "任务图" : "Task visual"} locale={locale} />
      <div className="task-tabs" role="tablist" aria-label={locale === "zh-CN" ? "点击任务列表" : "Tap task list"}>
        {topic.clickTasks.map((task) => (
          <button
            className={activeTaskId === task.id ? "active" : ""}
            key={task.id}
            type="button"
            onClick={() => dispatch({ type: "SELECT_CLICK_TASK", taskId: task.id })}
          >
            {task.title}
          </button>
        ))}
      </div>
      <div className="task-grid">
        {topic.clickTasks
          .filter((task) => task.id === activeTaskId)
          .map((task) => (
            <ClickTaskCard
              active
              key={task.id}
              task={task}
              locale={locale}
              selectedIds={state.taskSelectedIds[task.id] ?? []}
              result={state.taskResults[task.id] ?? "idle"}
              message={state.taskMessages[task.id]}
              onSelectTask={(taskId) => dispatch({ type: "SELECT_CLICK_TASK", taskId })}
              onClickOption={(taskId, optionId) => dispatch({ type: "CLICK_TASK_OPTION", taskId, optionId })}
            />
          ))}
      </div>
    </article>
  );
}
