import { useState } from "react";
import { Text, View } from "@tarojs/components";
import { resolveVisualEvidence, type ClickTask, type TaskResult, type Topic, type VisualEvidenceState, type VisualSlot } from "@yutou/kids-content";
import { TopicVisual } from "./TopicVisual";
import "./ClickTaskCard.scss";

function optionLabel(id: string) {
  return id.replace(/-/g, " ");
}

export function ClickTaskCard({ task, topic, visualSlot, locale }: { task: ClickTask; topic: Topic; visualSlot?: VisualSlot | null; locale: string }) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [result, setResult] = useState<TaskResult>("idle");
  const [message, setMessage] = useState("");
  const [evidence, setEvidence] = useState<VisualEvidenceState | null>(null);

  function resolveWrongHint(optionId?: string) {
    if (optionId && task.wrongHints && optionId in task.wrongHints) return task.wrongHints[optionId];
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
      setMessage(task.successCopy ?? (locale === "en-US" ? "Correct! Try explaining it to your grown-up." : "答对啦！你可以试着讲给爸爸妈妈听。"));
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
      setMessage(complete ? task.successCopy ?? (locale === "en-US" ? "You found them all!" : "找齐啦！") : task.prompt ?? task.title);
      updateEvidence(optionId, next, nextResult);
      return;
    }
    setResult("wrong");
    setMessage(resolveWrongHint(optionId));
    updateEvidence(optionId, [optionId], "wrong");
  }

  function handleSequence(optionId: string) {
    const expected = task.correctSequence?.[selectedIds.length];
    if (optionId !== expected) {
      setSelectedIds([]);
      setResult("wrong");
      setMessage(resolveWrongHint(optionId));
      updateEvidence(optionId, [], "wrong");
      return;
    }

    const next = [...selectedIds, optionId];
    setSelectedIds(next);
    const complete = next.length === task.correctSequence?.length;
    const nextResult = complete ? "complete" : "partial";
    setResult(nextResult);
    setMessage(complete ? task.successCopy ?? (locale === "en-US" ? "The sequence is complete!" : "顺序完成啦！") : task.prompt ?? task.title);
    updateEvidence(optionId, next, nextResult);
  }

  function handleOption(optionId: string) {
    if (task.type === "singleChoice") handleSingleChoice(optionId);
    if (task.type === "findTarget") handleFindTarget(optionId);
    if (task.type === "sequenceClick") handleSequence(optionId);
  }

  const options =
    task.options ??
    [...(task.targetIds ?? []), ...(task.decoyIds ?? [])].map((id) => ({
      id,
      label: optionLabel(id),
    }));

  return (
    <View className={`click-task ${result}`}>
      <TopicVisual
        slot={(evidence ? topic.visualSlots?.find((slot) => slot.id === evidence.visualSlotId) : visualSlot) ?? visualSlot}
        evidence={evidence}
        fallbackAlt={task.title}
        locale={locale === "en-US" ? "en-US" : "zh-CN"}
      />
      <Text className="click-task-title">{task.title}</Text>
      {task.prompt ? <Text className="click-task-prompt">{task.prompt}</Text> : null}
      <View className="click-task-options">
        {options.map((option) => (
          <View
            className={`click-task-option ${selectedIds.includes(option.id) ? "selected" : ""}`}
            key={option.id}
            data-task-option-id={option.id}
            data-evidence-source={`clickTasks.${task.id}.options.${option.id}`}
            onClick={() => handleOption(option.id)}
          >
            <Text>{option.label}</Text>
          </View>
        ))}
      </View>
      {message ? <Text className="click-task-message">{message}</Text> : null}
    </View>
  );
}
