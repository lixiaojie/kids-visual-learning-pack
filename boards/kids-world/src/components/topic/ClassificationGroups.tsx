import type { Topic } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";

type Props = {
  groups: Topic["classificationGroups"];
  activeGroupId?: string;
  locale: string;
};

export function ClassificationGroups({ groups, activeGroupId, locale }: Props) {
  return (
    <article className="panel">
      <SectionHeader title={locale === "zh-CN" ? "分类线索" : "Sorting clues"} />
      <div className="group-list">
        {groups.map((group) => (
          <button
            className={activeGroupId === group.id ? "group-card active" : "group-card"}
            key={group.id}
            type="button"
          >
            <strong>{group.name}</strong>
            <span>{group.childExplanation}</span>
          </button>
        ))}
      </div>
    </article>
  );
}
