import { Text, View } from "@tarojs/components";
import type { ClickTask, Locale, TaskResult } from "@yutou/kids-content";
import "./ClickTaskCard.scss";

function optionLabel(id: string) {
  return id.replace(/-/g, " ");
}

type Props = {
  task: ClickTask;
  locale: Locale;
  active: boolean;
  selectedIds: string[];
  result: TaskResult;
  message?: string;
  onSelectTask: (taskId: string) => void;
  onClickOption: (taskId: string, optionId: string) => void;
};

export function ClickTaskCard({ task, active, selectedIds, result, message, onSelectTask, onClickOption }: Props) {
  const options =
    task.options ??
    [...(task.targetIds ?? []), ...(task.decoyIds ?? [])].map((id) => ({
      id,
      label: optionLabel(id),
    }));

  return (
    <View className={`click-task ${active ? "active" : ""} ${result}`} onClick={() => onSelectTask(task.id)} data-evidence-source={`clickTasks.${task.id}`}>
      <Text className="click-task-title">{task.title}</Text>
      {task.prompt ? <Text className="click-task-prompt">{task.prompt}</Text> : null}
      <View className="click-task-options">
        {options.map((option) => (
          <View
            className={`click-task-option ${selectedIds.includes(option.id) ? "selected" : ""}`}
            key={option.id}
            data-task-option-id={option.id}
            data-evidence-source={`clickTasks.${task.id}.options.${option.id}`}
            onClick={(event) => {
              event.stopPropagation();
              onClickOption(task.id, option.id);
            }}
          >
            <Text>{option.label}</Text>
          </View>
        ))}
      </View>
      {message ? <Text className="click-task-message">{message}</Text> : null}
    </View>
  );
}
