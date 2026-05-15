import { useState } from "react";
import { Search } from "lucide-react";
import { resolveVisualEvidence } from "@yutou/kids-content";
import type { ClickTask, TaskResult, Topic, VisualEvidenceState, VisualSlot } from "../../types/topic";
import { TopicVisual } from "./TopicVisual";

export function ClickTaskCard({ task, topic, visualSlot, locale }: { task: ClickTask; topic: Topic; visualSlot?: VisualSlot | null; locale: string }) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [result, setResult] = useState<TaskResult>("idle");
  const [message, setMessage] = useState("");
  const [evidence, setEvidence] = useState<VisualEvidenceState | null>(null);

  function resolveWrongHint(optionId?: string) {
    if (optionId && task.wrongHints && optionId in task.wrongHints) return task.wrongHints[optionId as keyof typeof task.wrongHints];
    return task.wrongHint ?? (locale === "en-US" ? "Look for one more clue and try again." : "再观察一个线索试试看。");
  }

  function updateEvidence(optionId: string, nextSelectedIds: string[], nextResult: TaskResult) {
    setEvidence(
      resolveVisualEvidence(topic, {
        source: `clickTasks.${task.id}.options.${optionId}`,
        selectedIds: nextSelectedIds,
        result: nextResult,
        locale: locale === "en-US" ? "en-US" : "zh-CN",
      }),
    );
  }

  function handleSingleChoice(optionId: string) {
    if (optionId === task.correctOptionId) {
      setResult("correct");
      setMessage(task.successCopy ?? "");
      setSelectedIds([optionId]);
      updateEvidence(optionId, [optionId], "correct");
      return;
    }
    setResult("wrong");
    setMessage(resolveWrongHint(optionId));
    setSelectedIds([optionId]);
    updateEvidence(optionId, [optionId], "wrong");
  }

  function handleFindTarget(optionId: string) {
    if (task.targetIds?.includes(optionId)) {
      const next = Array.from(new Set([...selectedIds, optionId]));
      setSelectedIds(next);
      const complete = task.targetIds.every((id) => next.includes(id));
      const nextResult = complete ? "complete" : "partial";
      setResult(nextResult);
      setMessage(complete ? task.successCopy ?? "" : task.prompt ?? task.title);
      updateEvidence(optionId, next, nextResult);
      return;
    }
    setResult("wrong");
    setMessage(resolveWrongHint(optionId));
    updateEvidence(optionId, [optionId], "wrong");
  }

  function handleSequence(optionId: string) {
    const next = [...selectedIds, optionId];
    const expected = task.correctSequence?.[selectedIds.length];
    if (optionId !== expected) {
      setSelectedIds([]);
      setResult("wrong");
      setMessage(resolveWrongHint(optionId));
      updateEvidence(optionId, [], "wrong");
      return;
    }
    setSelectedIds(next);
    const complete = next.length === task.correctSequence?.length;
    const nextResult = complete ? "complete" : "partial";
    setResult(nextResult);
    setMessage(complete ? task.successCopy ?? "" : task.prompt ?? task.title);
    updateEvidence(optionId, next, nextResult);
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
      <TopicVisual
        slot={(evidence ? topic.visualSlots?.find((slot) => slot.id === evidence.visualSlotId) : visualSlot) ?? visualSlot}
        evidence={evidence}
        fallbackAlt={task.title}
        locale={locale === "en-US" ? "en-US" : "zh-CN"}
      />
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
