import { useState } from "react";
import { Text, View } from "@tarojs/components";
import type { ClickTask, TaskResult } from "@yutou/kids-content";
import "./ClickTaskCard.scss";

function optionLabel(id: string) {
  return id.replace(/-/g, " ");
}

export function ClickTaskCard({ task }: { task: ClickTask }) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [result, setResult] = useState<TaskResult>("idle");
  const [message, setMessage] = useState("");

  function resolveWrongHint(optionId?: string) {
    if (optionId && task.wrongHints && optionId in task.wrongHints) return task.wrongHints[optionId];
    return task.wrongHint ?? "再观察一个线索试试看。";
  }

  function handleSingleChoice(optionId: string) {
    if (optionId === task.correctOptionId) {
      setResult("correct");
      setMessage(task.successCopy ?? "答对啦！你可以试着讲给爸爸妈妈听。");
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
      setMessage(complete ? task.successCopy ?? "找齐啦！" : task.prompt ?? task.title);
      return;
    }
    setResult("wrong");
    setMessage(resolveWrongHint(optionId));
  }

  function handleSequence(optionId: string) {
    const expected = task.correctSequence?.[selectedIds.length];
    if (optionId !== expected) {
      setSelectedIds([]);
      setResult("wrong");
      setMessage(resolveWrongHint(optionId));
      return;
    }

    const next = [...selectedIds, optionId];
    setSelectedIds(next);
    const complete = next.length === task.correctSequence?.length;
    setResult(complete ? "correct" : "idle");
    setMessage(complete ? task.successCopy ?? "顺序完成啦！" : task.prompt ?? task.title);
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
      <Text className="click-task-title">{task.title}</Text>
      {task.prompt ? <Text className="click-task-prompt">{task.prompt}</Text> : null}
      <View className="click-task-options">
        {options.map((option) => (
          <View
            className={`click-task-option ${selectedIds.includes(option.id) ? "selected" : ""}`}
            key={option.id}
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
