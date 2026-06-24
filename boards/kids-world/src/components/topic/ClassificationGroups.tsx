import type { Topic, VisualEvidenceState, VisualSlot } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";
import { TopicVisual } from "./TopicVisual";

type Props = {
  topic: Topic;
  groups: Topic["classificationGroups"];
  activeGroupId?: string;
  evidence?: VisualEvidenceState | null;
  visualSlot?: VisualSlot | null;
  onSelectGroup?: (id: string) => void;
  locale: string;
};

export function ClassificationGroups({ groups, activeGroupId, evidence, visualSlot, onSelectGroup, locale }: Props) {
  const activeGroup = groups.find((group) => group.id === activeGroupId) ?? groups[0];
  const visualSupport = activeGroup
    ? {
        title: activeGroup.name,
        body: activeGroup.childExplanation,
        note: activeGroup.parentNote,
      }
    : null;

  return (
    <article className="panel interaction-panel" id="topic-classification">
      <SectionHeader title={locale === "zh-CN" ? "分类线索" : "Sorting clues"} />
      <div className="interaction-controls">
        <div className="group-list node-strip">
          {groups.map((group, index) => (
            <button
              className={activeGroupId === group.id ? "group-card node-button active" : "group-card node-button"}
              key={group.id}
              type="button"
              data-evidence-source={`classificationGroups.${group.id}`}
              onClick={() => onSelectGroup?.(group.id)}
            >
              <span className="node-index">{index + 1}</span>
              <strong className="node-label">{group.name}</strong>
            </button>
          ))}
        </div>
      </div>
      <TopicVisual slot={visualSlot} evidence={evidence} fallbackAlt={locale === "zh-CN" ? "分类证据图" : "Classification evidence"} locale={locale === "en-US" ? "en-US" : "zh-CN"} visualSupport={visualSupport} />
    </article>
  );
}
