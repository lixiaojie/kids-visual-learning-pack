import { Text, View } from "@tarojs/components";
import type { Locale, Topic, TopicInteractionAction, TopicInteractionState, TopicPresentation } from "@yutou/kids-content";
import { ClickTaskCard } from "./ClickTaskCard";
import { TopicVisual } from "./TopicVisual";
import "./ClickTaskDeck.scss";

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
    <View className="section" id="topic-tasks">
      <Text className="section-title">{locale === "zh-CN" ? "点击任务" : "Tap tasks"}</Text>
      <TopicVisual slot={taskVisualSlot} evidence={taskEvidence} fallbackAlt={locale === "zh-CN" ? "任务图" : "Task visual"} locale={locale} />
      <View className="click-task-tabs">
        {topic.clickTasks.map((task) => (
          <View
            className={`click-task-tab ${activeTaskId === task.id ? "active" : ""}`}
            key={task.id}
            onClick={() => dispatch({ type: "SELECT_CLICK_TASK", taskId: task.id })}
          >
            <Text>{task.title}</Text>
          </View>
        ))}
      </View>
      <View className="task-stack">
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
      </View>
    </View>
  );
}
