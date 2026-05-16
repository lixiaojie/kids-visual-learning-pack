import { Dna } from "lucide-react";
import type { Topic, VisualEvidenceState, VisualSlot } from "../../types/topic";
import { SectionHeader } from "../shared/SectionHeader";
import { TopicVisual } from "./TopicVisual";

type Props = {
  topic: Topic;
  objects: Topic["representativeObjects"];
  activeObjectId: string;
  onSelectObject: (id: string) => void;
  visualSlot?: VisualSlot | null;
  evidence?: VisualEvidenceState | null;
  locale: string;
};

export function RepresentativeObjects({ objects, activeObjectId, onSelectObject, visualSlot, evidence, locale }: Props) {
  const activeObject = objects.find((item) => item.id === activeObjectId) ?? objects[0];

  return (
    <article className="panel interaction-panel" id="topic-objects">
      <SectionHeader title={locale === "zh-CN" ? "对象卡" : "Object cards"} />
      <TopicVisual slot={visualSlot} evidence={evidence} fallbackAlt={locale === "zh-CN" ? "代表对象观察图" : "Representative object visual"} locale={locale === "en-US" ? "en-US" : "zh-CN"} />
      <div className="interaction-controls">
        <div className="object-grid">
          {objects.map((object) => (
            <button
              className={activeObjectId === object.id ? "object-card active" : "object-card"}
              key={object.id}
              type="button"
              data-evidence-source={`representativeObjects.${object.id}`}
              onClick={() => onSelectObject(object.id)}
            >
              <Dna size={20} />
              <strong>{object.name}</strong>
              <small>{object.visualHint}</small>
            </button>
          ))}
        </div>
        {activeObject && (
          <div className="object-detail">
            <strong>{activeObject.name}</strong>
            <span>{activeObject.childExplanation}</span>
            <small>{activeObject.commonMisread}</small>
          </div>
        )}
      </div>
    </article>
  );
}
