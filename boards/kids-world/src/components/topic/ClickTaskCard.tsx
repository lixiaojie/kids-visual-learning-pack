import { useState } from "react";
import { Search } from "lucide-react";
import type { ClickTask, TaskResult } from "../../types/topic";

export function ClickTaskCard({ task }: { task: ClickTask }) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [result, setResult] = useState<TaskResult>("idle");
  const [message, setMessage] = useState("");

  function resolveWrongHint(optionId?: string) {
    if (optionId && task.wrongHints && optionId in task.wrongHints) return task.wrongHints[optionId as keyof typeof task.wrongHints];
    return task.wrongHint ?? "再观察一个线索试试看。";
  }

  function handleSingleChoice(optionId: string) {
    if (optionId === task.correctOptionId) {
      setResult("correct");
      setMessage(task.successCopy ?? "");
      return;
    }
    setResult("wrong");
    setMessage(resolveWrongHint(optionId));
  }

  function handleFindTarget(optionId: string) {
    if (task.targetIds?.includes(optionId)) {
      const next = Array.from(new Set([...selectedIds, optionId]));
      setSelectedIds(next);
      const complete = task.targetIds.every((id) => next.includes(id));
      setResult(complete ? "correct" : "idle");
      setMessage(complete ? task.successCopy ?? "" : task.prompt ?? task.title);
      return;
    }
    setResult("wrong");
    setMessage(resolveWrongHint(optionId));
  }

  function handleSequence(optionId: string) {
    const next = [...selectedIds, optionId];
    const expected = task.correctSequence?.[selectedIds.length];
    if (optionId !== expected) {
      setSelectedIds([]);
      setResult("wrong");
      setMessage(resolveWrongHint(optionId));
      return;
    }
    setSelectedIds(next);
    const complete = next.length === task.correctSequence?.length;
    setResult(complete ? "correct" : "idle");
    setMessage(complete ? task.successCopy ?? "" : task.prompt ?? task.title);
  }

  function handleClick(optionId: string) {
    if (task.type === "singleChoice") handleSingleChoice(optionId);
    if (task.type === "findTarget") handleFindTarget(optionId);
    if (task.type === "sequenceClick") handleSequence(optionId);
  }

  const options =
    task.options ??
    [...(task.targetIds ?? []), ...(task.decoyIds ?? [])].map((id) => ({
      id,
      label: id.replace(/-/g, " "),
    }));

  return (
    <div className={`task-card ${result}`}>
      <Search size={20} />
      <strong>{task.title}</strong>
      {task.prompt && <span>{task.prompt}</span>}
      <div className="task-options">
        {options.map((option) => (
          <button
            className={selectedIds.includes(option.id) ? "selected" : ""}
            key={option.id}
            type="button"
            onClick={() => handleClick(option.id)}
          >
            {option.label}
          </button>
        ))}
      </div>
      {message && <p>{message}</p>}
    </div>
  );
}
