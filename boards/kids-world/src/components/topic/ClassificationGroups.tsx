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
  return (
    <article className="panel" id="topic-classification">
      <SectionHeader title={locale === "zh-CN" ? "分类线索" : "Sorting clues"} />
      <TopicVisual slot={visualSlot} evidence={evidence} fallbackAlt={locale === "zh-CN" ? "分类证据图" : "Classification evidence"} locale={locale === "en-US" ? "en-US" : "zh-CN"} />
      <div className="group-list">
        {groups.map((group) => (
          <button
            className={activeGroupId === group.id ? "group-card active" : "group-card"}
            key={group.id}
            type="button"
            data-evidence-source={`classificationGroups.${group.id}`}
            onClick={() => onSelectGroup?.(group.id)}
          >
            <strong>{group.name}</strong>
            <span>{group.childExplanation}</span>
          </button>
        ))}
      </div>
    </article>
  );
}
