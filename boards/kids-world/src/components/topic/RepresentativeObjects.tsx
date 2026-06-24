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
  const visualSupport = activeObject
    ? {
        title: activeObject.name,
        body: activeObject.childExplanation,
        note: activeObject.commonMisread ?? activeObject.visualHint,
      }
    : null;

  return (
    <article className="panel interaction-panel" id="topic-objects">
      <SectionHeader title={locale === "zh-CN" ? "对象卡" : "Object cards"} />
      <div className="interaction-controls">
        <div className="object-grid node-strip">
          {objects.map((object, index) => (
            <button
              className={activeObjectId === object.id ? "object-card node-button active" : "object-card node-button"}
              key={object.id}
              type="button"
              data-evidence-source={`representativeObjects.${object.id}`}
              onClick={() => onSelectObject(object.id)}
            >
              <span className="node-index">{index + 1}</span>
              <strong className="node-label">{object.name}</strong>
            </button>
          ))}
        </div>
      </div>
      <TopicVisual slot={visualSlot} evidence={evidence} fallbackAlt={locale === "zh-CN" ? "代表对象观察图" : "Representative object visual"} locale={locale === "en-US" ? "en-US" : "zh-CN"} visualSupport={visualSupport} />
    </article>
  );
}
