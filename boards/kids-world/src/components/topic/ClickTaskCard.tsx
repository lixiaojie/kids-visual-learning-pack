import { Search } from "lucide-react";
import type { ClickTask, Locale, TaskResult } from "../../types/topic";

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
      label: id.replace(/-/g, " "),
    }));

  return (
    <div className={`task-card ${active ? "active" : ""} ${result}`} onClick={() => onSelectTask(task.id)} data-evidence-source={`clickTasks.${task.id}`}>
      <Search size={20} />
      <strong>{task.title}</strong>
      {task.prompt && <span>{task.prompt}</span>}
      <div className="task-options">
        {options.map((option) => (
          <button
            className={selectedIds.includes(option.id) ? "selected" : ""}
            key={option.id}
            type="button"
            data-task-option-id={option.id}
            data-evidence-source={`clickTasks.${task.id}.options.${option.id}`}
            onClick={(event) => {
              event.stopPropagation();
              onClickOption(task.id, option.id);
            }}
          >
            {option.label}
          </button>
        ))}
      </div>
      {message && <p>{message}</p>}
    </div>
  );
}
